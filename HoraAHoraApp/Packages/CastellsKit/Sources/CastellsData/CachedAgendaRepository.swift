import Foundation
import SwiftData
import CastellsDomain

@MainActor
public final class CachedAgendaRepository: AgendaRepository {
    public let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!
    private let context: ModelContext
    private let remoteService: any AgendaRemoteService

    public init(container: ModelContainer, remoteService: any AgendaRemoteService) {
        self.context = ModelContext(container)
        self.remoteService = remoteService
    }

    public func cachedEvents(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?
    ) throws -> [CastellEvent] {
        try cachedItems(
            from: from,
            to: to,
            group: group,
            municipality: municipality,
            limit: .max
        )
    }

    public func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage {
        do {
            let page = try await remoteService.events(
                from: from,
                to: to,
                group: group,
                municipality: municipality,
                cursor: cursor,
                limit: limit,
                forceRefresh: forceRefresh
            )
            if page.sourceStatus == .unavailable {
                try purgeDemoItems()
            }
            try store(
                page.items,
                from: from,
                to: to,
                replacingCompleteRange: cursor == nil
                    && page.nextCursor == nil
                    && group == nil
                    && municipality == nil
                    && page.sourceStatus == .active
            )
            if page.items.isEmpty, page.sourceStatus == .unavailable, cursor == nil {
                let cached = try cachedItems(
                    from: from, to: to, group: group, municipality: municipality, limit: limit
                )
                if !cached.isEmpty {
                    return AgendaPage(
                        items: cached,
                        nextCursor: nil,
                        officialURL: page.officialURL,
                        fromCache: true,
                        sourceStatus: .unavailable
                    )
                }
            }
            return page
        } catch {
            guard cursor == nil else { throw error }
            let cached = try cachedItems(
                from: from, to: to, group: group, municipality: municipality, limit: limit
            )
            guard !cached.isEmpty else { throw error }
            return AgendaPage(
                items: cached,
                nextCursor: nil,
                officialURL: officialURL,
                fromCache: true,
                sourceStatus: .active
            )
        }
    }

    private func store(
        _ items: [CastellEvent],
        from: Date,
        to: Date,
        replacingCompleteRange: Bool
    ) throws {
        let existing = try context.fetch(FetchDescriptor<AgendaCacheRecord>())
        var byID = Dictionary(uniqueKeysWithValues: existing.map { ($0.id, $0) })
        for item in items {
            if let record = byID[item.id] {
                record.update(with: item)
            } else {
                let record = AgendaCacheRecord(item: item)
                context.insert(record)
                byID[item.id] = record
            }
        }
        if replacingCompleteRange {
            let lower = agendaDateString(from)
            let upper = agendaDateString(to)
            let incomingIDs = Set(items.map(\.id))
            for record in existing
            where lower <= record.localDate && record.localDate <= upper && !incomingIDs.contains(record.id) {
                context.delete(record)
            }
        }
        try context.save()
    }

    private func cachedItems(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        limit: Int
    ) throws -> [CastellEvent] {
        let lower = agendaDateString(from)
        let upper = agendaDateString(to)
        let groupKey = group.map(searchKey)
        let municipalityKey = municipality.map(searchKey)
        return try context.fetch(FetchDescriptor<AgendaCacheRecord>())
            .filter { record in
                !Self.isDemo(record)
                    && lower <= record.localDate && record.localDate <= upper
                    && (groupKey == nil || record.participatingGroups.contains { searchKey($0) == groupKey })
                    && (municipalityKey == nil || searchKey(record.municipality) == municipalityKey)
            }
            .compactMap(Self.domainItem)
            .sorted {
                if $0.localDate == $1.localDate { return $0.sourceOrder < $1.sourceOrder }
                return $0.localDate < $1.localDate
            }
            .prefix(limit)
            .map { $0 }
    }

    private func purgeDemoItems() throws {
        let records = try context.fetch(FetchDescriptor<AgendaCacheRecord>())
        for record in records where Self.isDemo(record) {
            context.delete(record)
        }
        try context.save()
    }

    private static func isDemo(_ record: AgendaCacheRecord) -> Bool {
        record.sourceID == "cccc-fixture"
            || record.title.localizedCaseInsensitiveContains("demostració")
            || record.notes.localizedCaseInsensitiveContains("dada simulada")
    }

    private static func domainItem(_ record: AgendaCacheRecord) -> CastellEvent? {
        guard let sourceURL = URL(string: record.sourceURL) else { return nil }
        return CastellEvent(
            id: record.id,
            sourceID: record.sourceID,
            externalID: record.externalID,
            title: record.title,
            localDate: record.localDate,
            startsAt: record.startsAt,
            timeLabel: record.timeLabel,
            timezone: record.timezone,
            venue: record.venue,
            municipality: record.municipality,
            participatingGroups: record.participatingGroups,
            notes: record.notes,
            sourceURL: sourceURL,
            sourceOrder: record.sourceOrder,
            attribution: record.attribution,
            revision: record.revision,
            updatedAt: record.updatedAt
        )
    }
}

private func searchKey(_ value: String) -> String {
    value.folding(options: [.caseInsensitive, .diacriticInsensitive], locale: Locale(identifier: "ca"))
        .split(whereSeparator: \.isWhitespace)
        .joined(separator: " ")
}
