import Foundation
import SwiftData
import CastellsDomain

@MainActor
public final class CachedHourByHourRepository: HourByHourRepository {
    private let context: ModelContext
    private let remoteService: any HourByHourRemoteService

    public init(container: ModelContainer, remoteService: any HourByHourRemoteService) {
        self.context = ModelContext(container)
        self.remoteService = remoteService
    }

    public func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        do {
            let page = try await remoteService.page(cursor: cursor, limit: limit, forceRefresh: forceRefresh)
            try store(page.items)
            return page
        } catch {
            guard cursor == nil else { throw error }
            let cached = try cachedItems(limit: limit)
            guard !cached.isEmpty else { throw error }
            return HourByHourPage(items: cached, nextCursor: nil, fromCache: true)
        }
    }

    private func store(_ items: [HourByHourItem]) throws {
        let existing = try context.fetch(FetchDescriptor<HourByHourCacheRecord>())
        var byID = Dictionary(uniqueKeysWithValues: existing.map { ($0.id, $0) })
        for item in items {
            if let record = byID[item.id] {
                record.update(with: item)
            } else {
                let record = HourByHourCacheRecord(item: item)
                context.insert(record)
                byID[item.id] = record
            }
        }
        try context.save()
    }

    private func cachedItems(limit: Int) throws -> [HourByHourItem] {
        let records = try context.fetch(FetchDescriptor<HourByHourCacheRecord>())
        return records
            .compactMap(Self.domainItem)
            .sorted {
                let left = $0.publishedAt ?? $0.updatedAt
                let right = $1.publishedAt ?? $1.updatedAt
                if left == right { return $0.sourceOrder < $1.sourceOrder }
                return left > right
            }
            .prefix(limit)
            .map { $0 }
    }

    private static func domainItem(_ record: HourByHourCacheRecord) -> HourByHourItem? {
        guard let articleURL = URL(string: record.articleURL) else { return nil }
        let actionURL = record.actionURL.flatMap(URL.init(string:))
        return HourByHourItem(
            id: record.id,
            sourceID: record.sourceID,
            externalID: record.externalID,
            title: record.title,
            displayTitle: record.displayTitle ?? record.title,
            summary: record.summary,
            publishedAt: record.publishedAt,
            sourceOrder: record.sourceOrder,
            articleURL: articleURL,
            actionURL: actionURL,
            attribution: record.attribution,
            createdAt: record.createdAt,
            updatedAt: record.updatedAt
        )
    }
}
