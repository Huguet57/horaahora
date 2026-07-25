import Foundation
import XCTest
import CastellsDomain
@testable import FeatureAgenda

@MainActor
final class AgendaPageLoaderTests: XCTestCase {
    func testLoadsEveryPageAndOnlyForcesTheFirstRequest() async throws {
        let repository = PaginatedAgendaRepositoryStub()
        let loader = AgendaPageLoader(repository: repository)

        let result = try await loader.fetch(
            range: (agendaDate("2026-07-01"), agendaDate("2026-07-31")),
            forceRefresh: true
        )

        XCTAssertEqual(result.items.map(\.externalID), ["first", "second"])
        XCTAssertEqual(repository.requests.map(\.cursor), [nil, "next"])
        XCTAssertEqual(repository.requests.map(\.forceRefresh), [true, false])
        XCTAssertFalse(result.fromCache)
        XCTAssertEqual(result.sourceStatus, .unavailable)
    }
}

@MainActor
private final class PaginatedAgendaRepositoryStub: AgendaRepository {
    let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!
    var requests: [(cursor: String?, forceRefresh: Bool)] = []

    func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage {
        requests.append((cursor: cursor, forceRefresh: forceRefresh))
        if cursor == nil {
            return AgendaPage(
                items: [
                    makeAgendaEvent(id: "first", localDate: "2026-07-01", title: "First")
                ],
                nextCursor: "next",
                officialURL: officialURL,
                fromCache: true,
                sourceStatus: .active
            )
        }
        return AgendaPage(
            items: [
                makeAgendaEvent(id: "second", localDate: "2026-07-02", title: "Second")
            ],
            nextCursor: nil,
            officialURL: officialURL,
            fromCache: false,
            sourceStatus: .unavailable
        )
    }
}
