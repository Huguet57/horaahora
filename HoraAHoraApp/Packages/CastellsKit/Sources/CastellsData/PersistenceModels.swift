import Foundation
import SwiftData
import CastellsDomain

@Model
final class ConversationRecord {
    @Attribute(.unique) var id: UUID
    var title: String
    var createdAt: Date
    var updatedAt: Date
    @Relationship(deleteRule: .cascade, inverse: \MessageRecord.conversation)
    var messages: [MessageRecord]

    init(id: UUID = UUID(), title: String, createdAt: Date = .now, updatedAt: Date = .now) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messages = []
    }
}

@Model
final class MessageRecord {
    @Attribute(.unique) var id: UUID
    var roleRaw: String
    var content: String
    var createdAt: Date
    var deliveryStateRaw: String
    var calculationData: Data?
    var conversation: ConversationRecord?

    init(
        id: UUID = UUID(),
        roleRaw: String,
        content: String,
        createdAt: Date = .now,
        deliveryStateRaw: String,
        calculationData: Data? = nil,
        conversation: ConversationRecord? = nil
    ) {
        self.id = id
        self.roleRaw = roleRaw
        self.content = content
        self.createdAt = createdAt
        self.deliveryStateRaw = deliveryStateRaw
        self.calculationData = calculationData
        self.conversation = conversation
    }
}

@Model
final class HourByHourCacheRecord {
    @Attribute(.unique) var id: String
    var sourceID: String
    var externalID: String
    var title: String
    var displayTitle: String?
    var summary: String
    var publishedAt: Date?
    var sourceOrder: Int
    var articleURL: String
    var actionURL: String?
    var attribution: String
    var createdAt: Date
    var updatedAt: Date

    init(item: CastellsDomain.HourByHourItem) {
        self.id = item.id
        self.sourceID = item.sourceID
        self.externalID = item.externalID
        self.title = item.title
        self.displayTitle = item.displayTitle
        self.summary = item.summary
        self.publishedAt = item.publishedAt
        self.sourceOrder = item.sourceOrder
        self.articleURL = item.articleURL.absoluteString
        self.actionURL = item.actionURL?.absoluteString
        self.attribution = item.attribution
        self.createdAt = item.createdAt
        self.updatedAt = item.updatedAt
    }

    func update(with item: CastellsDomain.HourByHourItem) {
        title = item.title
        displayTitle = item.displayTitle
        summary = item.summary
        publishedAt = item.publishedAt
        sourceOrder = item.sourceOrder
        articleURL = item.articleURL.absoluteString
        actionURL = item.actionURL?.absoluteString
        attribution = item.attribution
        updatedAt = item.updatedAt
    }
}

@Model
final class AgendaCacheRecord {
    @Attribute(.unique) var id: String
    var sourceID: String
    var externalID: String
    var title: String
    var localDate: String
    var startsAt: Date?
    var timeLabel: String
    var timezone: String
    var venue: String
    var municipality: String
    var participatingGroups: [String]
    var notes: String
    var sourceURL: String
    var sourceOrder: Int
    var attribution: String
    var revision: String
    var updatedAt: Date

    init(item: CastellsDomain.CastellEvent) {
        self.id = item.id
        self.sourceID = item.sourceID
        self.externalID = item.externalID
        self.title = item.title
        self.localDate = item.localDate
        self.startsAt = item.startsAt
        self.timeLabel = item.timeLabel
        self.timezone = item.timezone
        self.venue = item.venue
        self.municipality = item.municipality
        self.participatingGroups = item.participatingGroups
        self.notes = item.notes
        self.sourceURL = item.sourceURL.absoluteString
        self.sourceOrder = item.sourceOrder
        self.attribution = item.attribution
        self.revision = item.revision
        self.updatedAt = item.updatedAt
    }

    func update(with item: CastellsDomain.CastellEvent) {
        title = item.title
        localDate = item.localDate
        startsAt = item.startsAt
        timeLabel = item.timeLabel
        timezone = item.timezone
        venue = item.venue
        municipality = item.municipality
        participatingGroups = item.participatingGroups
        notes = item.notes
        sourceURL = item.sourceURL.absoluteString
        sourceOrder = item.sourceOrder
        attribution = item.attribution
        revision = item.revision
        updatedAt = item.updatedAt
    }
}
