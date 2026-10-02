import Foundation
import SwiftData

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

// MARK: - Legacy-only

// Earlier versions kept local copies of Hora a Hora and the Agenda in this same store, and those
// features now live in a separate app. These two entities stay in the schema, with exactly the
// same names and stored properties, only so that an upgrade opens an existing store as it is,
// without a migration, and the conversations survive. Nothing reads or writes them. Do not
// change them, and do not use them for anything new.

/// Legacy-only: see the note above.
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

    /// @Model needs an initializer; nothing creates these records any more.
    init(id: String) {
        self.id = id
        sourceID = ""
        externalID = ""
        title = ""
        summary = ""
        sourceOrder = 0
        articleURL = ""
        attribution = ""
        createdAt = .distantPast
        updatedAt = .distantPast
    }
}

/// Legacy-only: see the note above.
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

    /// @Model needs an initializer; nothing creates these records any more.
    init(id: String) {
        self.id = id
        sourceID = ""
        externalID = ""
        title = ""
        localDate = ""
        timeLabel = ""
        timezone = ""
        venue = ""
        municipality = ""
        participatingGroups = []
        notes = ""
        sourceURL = ""
        sourceOrder = 0
        attribution = ""
        revision = ""
        updatedAt = .distantPast
    }
}
