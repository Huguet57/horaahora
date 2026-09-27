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

/// The local copy of Hora a Hora. Only the internal app reads and writes it, through
/// CastellsInternalData, but the table stays in both apps so that the schema never changes.
@Model
public final class HourByHourCacheRecord {
    @Attribute(.unique) public var id: String
    public var sourceID: String
    public var externalID: String
    public var title: String
    public var displayTitle: String?
    public var summary: String
    public var publishedAt: Date?
    public var sourceOrder: Int
    public var articleURL: String
    public var actionURL: String?
    public var attribution: String
    public var createdAt: Date
    public var updatedAt: Date

    public init(item: CastellsDomain.HourByHourItem) {
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

    public func update(with item: CastellsDomain.HourByHourItem) {
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

/// The local copy of the Agenda. Only the internal app reads and writes it, through
/// CastellsInternalData, but the table stays in both apps so that the schema never changes.
@Model
public final class AgendaCacheRecord {
    @Attribute(.unique) public var id: String
    public var sourceID: String
    public var externalID: String
    public var title: String
    public var localDate: String
    public var startsAt: Date?
    public var timeLabel: String
    public var timezone: String
    public var venue: String
    public var municipality: String
    public var participatingGroups: [String]
    public var notes: String
    public var sourceURL: String
    public var sourceOrder: Int
    public var attribution: String
    public var revision: String
    public var updatedAt: Date

    public init(item: CastellsDomain.CastellEvent) {
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

    public func update(with item: CastellsDomain.CastellEvent) {
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
