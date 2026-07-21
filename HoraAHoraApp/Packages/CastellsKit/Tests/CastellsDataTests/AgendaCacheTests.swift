import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class AgendaCacheTests: XCTestCase {
    func testReadsThePersistedSnapshotWithoutCallingTheRemoteServiceAgain() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = SequencedAgendaRemote()
        let repository = CachedAgendaRepository(container: container, remoteService: remote)
        let day = ISO8601DateFormatter().date(from: "2026-07-21T00:00:00Z")!

        _ = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )
        let cached = try repository.cachedEvents(
            from: day, to: day, group: nil, municipality: nil
        )

        XCTAssertEqual(cached.map(\.title), ["Diada de prova"])
        XCTAssertEqual(remote.calls, 1)
    }

    func testReturnsNetworkEventsThenFallsBackToTheSelectedDayCache() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = SequencedAgendaRemote()
        let repository = CachedAgendaRepository(container: container, remoteService: remote)
        let day = ISO8601DateFormatter().date(from: "2026-07-21T00:00:00Z")!

        let fresh = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )
        XCTAssertEqual(fresh.items.map(\.title), ["Diada de prova"])
        XCTAssertFalse(fresh.fromCache)

        let cached = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )
        XCTAssertEqual(cached.items.map(\.title), ["Diada de prova"])
        XCTAssertTrue(cached.fromCache)
    }

    func testUnavailableSourceDoesNotErasePreviouslyCachedEvents() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = AvailableThenUnavailableAgendaRemote()
        let repository = CachedAgendaRepository(container: container, remoteService: remote)
        let day = ISO8601DateFormatter().date(from: "2026-07-21T00:00:00Z")!

        _ = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )
        let cached = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )

        XCTAssertEqual(cached.items.map(\.title), ["Diada de prova"])
        XCTAssertTrue(cached.fromCache)
        XCTAssertEqual(cached.sourceStatus, .unavailable)
    }

    func testUnavailableSourceRemovesPreviouslyCachedDemoEvents() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = DemoThenUnavailableAgendaRemote()
        let repository = CachedAgendaRepository(container: container, remoteService: remote)
        let day = ISO8601DateFormatter().date(from: "2026-07-21T00:00:00Z")!

        _ = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )
        let result = try await repository.events(
            from: day, to: day, group: nil, municipality: nil,
            cursor: nil, limit: 50, forceRefresh: false
        )

        XCTAssertTrue(result.items.isEmpty)
        XCTAssertEqual(result.sourceStatus, .unavailable)
    }
}

private final class SequencedAgendaRemote: AgendaRemoteService, @unchecked Sendable {
    private(set) var calls = 0

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        calls += 1
        if calls > 1 { throw URLError(.notConnectedToInternet) }
        return AgendaPage(
            items: [
                CastellEvent(
                    id: "event-1", sourceID: "cccc", externalID: "external-1",
                    title: "Diada de prova", localDate: "2026-07-21", startsAt: nil,
                    timeLabel: "Tarda", timezone: "Europe/Madrid", venue: "Plaça",
                    municipality: "Valls", participatingGroups: ["Colla A"], notes: "",
                    sourceURL: URL(string: "https://castellscat.cat/ca/agenda")!,
                    sourceOrder: 0,
                    attribution: "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                    revision: "r1", updatedAt: Date()
                )
            ],
            nextCursor: nil,
            officialURL: URL(string: "https://castellscat.cat/ca/agenda")!,
            fromCache: false,
            sourceStatus: .active
        )
    }
}

private final class AvailableThenUnavailableAgendaRemote: AgendaRemoteService, @unchecked Sendable {
    private let available = SequencedAgendaRemote()
    private var calls = 0

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        calls += 1
        if calls == 1 {
            return try await available.events(
                from: from, to: to, group: group, municipality: municipality,
                cursor: cursor, limit: limit, forceRefresh: forceRefresh
            )
        }
        return AgendaPage(
            items: [],
            nextCursor: nil,
            officialURL: URL(string: "https://castellscat.cat/ca/agenda")!,
            fromCache: true,
            sourceStatus: .unavailable
        )
    }
}

private final class DemoThenUnavailableAgendaRemote: AgendaRemoteService, @unchecked Sendable {
    private var calls = 0

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        calls += 1
        if calls > 1 {
            return AgendaPage(
                items: [], nextCursor: nil,
                officialURL: URL(string: "https://castellscat.cat/ca/agenda")!,
                fromCache: true, sourceStatus: .unavailable
            )
        }
        return AgendaPage(
            items: [
                CastellEvent(
                    id: "demo", sourceID: "cccc-fixture", externalID: "demo",
                    title: "Diada de demostració", localDate: "2026-07-21", startsAt: nil,
                    timeLabel: "Tarda", timezone: "Europe/Madrid", venue: "Plaça",
                    municipality: "Valls", participatingGroups: ["Colla demo"],
                    notes: "Dada simulada per al desenvolupament local.",
                    sourceURL: URL(string: "https://castellscat.cat/ca/agenda")!,
                    sourceOrder: 0, attribution: "Dades de demostració — no oficials",
                    revision: "r1", updatedAt: Date()
                )
            ],
            nextCursor: nil,
            officialURL: URL(string: "https://castellscat.cat/ca/agenda")!,
            fromCache: false,
            sourceStatus: .active
        )
    }
}
