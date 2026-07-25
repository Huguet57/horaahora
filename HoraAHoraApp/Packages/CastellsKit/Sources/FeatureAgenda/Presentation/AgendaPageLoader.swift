import Foundation
import CastellsDomain

typealias AgendaFetchResult = (
    items: [CastellEvent],
    fromCache: Bool,
    sourceStatus: AgendaSourceStatus
)

@MainActor
struct AgendaPageLoader {
    let repository: any AgendaRepository

    func fetch(
        range: (start: Date, end: Date),
        forceRefresh: Bool
    ) async throws -> AgendaFetchResult {
        var cursor: String?
        var collected: [CastellEvent] = []
        var allFromCache = true
        var statuses: [AgendaSourceStatus] = []

        repeat {
            let page = try await repository.events(
                from: range.start,
                to: range.end,
                group: nil,
                municipality: nil,
                cursor: cursor,
                limit: 100,
                forceRefresh: forceRefresh && cursor == nil
            )
            collected.append(contentsOf: page.items)
            allFromCache = allFromCache && page.fromCache
            statuses.append(page.sourceStatus)
            cursor = page.nextCursor
        } while cursor != nil

        return (
            collected,
            allFromCache,
            statuses.allSatisfy { $0 == .active } ? .active : .unavailable
        )
    }
}
