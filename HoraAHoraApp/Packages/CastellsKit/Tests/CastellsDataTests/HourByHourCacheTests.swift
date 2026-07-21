import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class HourByHourCacheTests: XCTestCase {
    func testReturnsNetworkItemsThenFallsBackToCache() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = SequencedHourByHourRemote()
        let repository = CachedHourByHourRepository(container: container, remoteService: remote)

        let fresh = try await repository.page(cursor: nil, limit: 30, forceRefresh: false)
        XCTAssertEqual(fresh.items.map(\.title), ["Notícia nova"])
        XCTAssertNil(fresh.items.first?.actionURL)
        XCTAssertFalse(fresh.fromCache)

        let cached = try await repository.page(cursor: nil, limit: 30, forceRefresh: false)
        XCTAssertEqual(cached.items.map(\.title), ["Notícia nova"])
        XCTAssertNil(cached.items.first?.actionURL)
        XCTAssertTrue(cached.fromCache)
    }
}

private final class SequencedHourByHourRemote: HourByHourRemoteService, @unchecked Sendable {
    private var calls = 0

    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        calls += 1
        if calls > 1 { throw URLError(.notConnectedToInternet) }
        let now = Date()
        return HourByHourPage(
            items: [
                HourByHourItem(
                    id: "1",
                    sourceID: "revista-castells",
                    externalID: "external",
                    title: "Notícia nova",
                    displayTitle: "Notícia nova",
                    summary: "Resum",
                    publishedAt: now,
                    sourceOrder: 0,
                    articleURL: URL(string: "https://example.com/article")!,
                    actionURL: nil,
                    attribution: "Revista Castells",
                    createdAt: now,
                    updatedAt: now
                )
            ],
            nextCursor: nil,
            fromCache: false
        )
    }
}
