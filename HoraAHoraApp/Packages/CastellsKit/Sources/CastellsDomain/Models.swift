import Foundation

public struct HourByHourItem: Identifiable, Codable, Hashable, Sendable {
    public let id: String
    public let sourceID: String
    public let externalID: String
    public let title: String
    public let displayTitle: String
    public let summary: String
    public let publishedAt: Date?
    public let sourceOrder: Int
    public let articleURL: URL
    public let actionURL: URL
    public let attribution: String
    public let createdAt: Date
    public let updatedAt: Date

    public init(
        id: String,
        sourceID: String,
        externalID: String,
        title: String,
        displayTitle: String,
        summary: String,
        publishedAt: Date?,
        sourceOrder: Int,
        articleURL: URL,
        actionURL: URL,
        attribution: String,
        createdAt: Date,
        updatedAt: Date
    ) {
        self.id = id
        self.sourceID = sourceID
        self.externalID = externalID
        self.title = title
        self.displayTitle = displayTitle
        self.summary = summary
        self.publishedAt = publishedAt
        self.sourceOrder = sourceOrder
        self.articleURL = articleURL
        self.actionURL = actionURL
        self.attribution = attribution
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

public struct HourByHourPage: Codable, Sendable {
    public let items: [HourByHourItem]
    public let nextCursor: String?
    public let fromCache: Bool

    public init(items: [HourByHourItem], nextCursor: String?, fromCache: Bool) {
        self.items = items
        self.nextCursor = nextCursor
        self.fromCache = fromCache
    }
}

public struct CastellEvent: Identifiable, Codable, Hashable, Sendable {
    public let id: String
    public let sourceID: String
    public let externalID: String
    public let title: String
    public let localDate: String
    public let startsAt: Date?
    public let timeLabel: String
    public let timezone: String
    public let venue: String
    public let municipality: String
    public let participatingGroups: [String]
    public let notes: String
    public let sourceURL: URL
    public let sourceOrder: Int
    public let attribution: String
    public let revision: String
    public let updatedAt: Date

    public init(
        id: String,
        sourceID: String,
        externalID: String,
        title: String,
        localDate: String,
        startsAt: Date?,
        timeLabel: String,
        timezone: String,
        venue: String,
        municipality: String,
        participatingGroups: [String],
        notes: String,
        sourceURL: URL,
        sourceOrder: Int,
        attribution: String,
        revision: String,
        updatedAt: Date
    ) {
        self.id = id
        self.sourceID = sourceID
        self.externalID = externalID
        self.title = title
        self.localDate = localDate
        self.startsAt = startsAt
        self.timeLabel = timeLabel
        self.timezone = timezone
        self.venue = venue
        self.municipality = municipality
        self.participatingGroups = participatingGroups
        self.notes = notes
        self.sourceURL = sourceURL
        self.sourceOrder = sourceOrder
        self.attribution = attribution
        self.revision = revision
        self.updatedAt = updatedAt
    }
}

public enum AgendaSourceStatus: String, Codable, Hashable, Sendable {
    case active
    case unavailable
}

public struct AgendaPage: Codable, Sendable {
    public let items: [CastellEvent]
    public let nextCursor: String?
    public let officialURL: URL
    public let fromCache: Bool
    public let sourceStatus: AgendaSourceStatus

    public init(
        items: [CastellEvent],
        nextCursor: String?,
        officialURL: URL,
        fromCache: Bool,
        sourceStatus: AgendaSourceStatus
    ) {
        self.items = items
        self.nextCursor = nextCursor
        self.officialURL = officialURL
        self.fromCache = fromCache
        self.sourceStatus = sourceStatus
    }
}

public enum ChatRole: String, Codable, Sendable {
    case user
    case assistant
}

public enum MessageDeliveryState: String, Codable, Sendable {
    case sending
    case sent
    case failed
}

public struct ChatMessage: Identifiable, Codable, Hashable, Sendable {
    public let id: UUID
    public let role: ChatRole
    public let content: String
    public let createdAt: Date
    public let deliveryState: MessageDeliveryState
    public let calculation: ChatResponse?

    public init(
        id: UUID,
        role: ChatRole,
        content: String,
        createdAt: Date,
        deliveryState: MessageDeliveryState,
        calculation: ChatResponse? = nil
    ) {
        self.id = id
        self.role = role
        self.content = content
        self.createdAt = createdAt
        self.deliveryState = deliveryState
        self.calculation = calculation
    }
}

public struct ChatConversationSummary: Identifiable, Codable, Hashable, Sendable {
    public let id: UUID
    public let title: String
    public let createdAt: Date
    public let updatedAt: Date

    public init(id: UUID, title: String, createdAt: Date, updatedAt: Date) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

public struct ChatConversation: Identifiable, Codable, Hashable, Sendable {
    public let id: UUID
    public let title: String
    public let createdAt: Date
    public let updatedAt: Date
    public let messages: [ChatMessage]

    public init(id: UUID, title: String, createdAt: Date, updatedAt: Date, messages: [ChatMessage]) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messages = messages
    }
}

public struct ChatRequestMessage: Codable, Hashable, Sendable {
    public let role: ChatRole
    public let content: String

    public init(role: ChatRole, content: String) {
        self.role = role
        self.content = content
    }
}

public struct ChatRequest: Codable, Sendable {
    public let conversationID: UUID
    public let installationID: String
    public let locale: String
    public let ruleset: String
    public let messages: [ChatRequestMessage]

    public init(
        conversationID: UUID,
        installationID: String,
        locale: String = "ca-ES",
        ruleset: String = "concurs-2026",
        messages: [ChatRequestMessage]
    ) {
        self.conversationID = conversationID
        self.installationID = installationID
        self.locale = locale
        self.ruleset = ruleset
        self.messages = Array(messages.suffix(12))
    }
}

public struct ScoredCastellResponse: Codable, Hashable, Sendable {
    public let input: String
    public let canonical: String?
    public let outcome: String
    public let points: Int
    public let counted: Bool
    public let reason: String?
}

public struct PerformanceResponse: Codable, Hashable, Sendable {
    public let label: String
    public let total: Int
    public let castells: [ScoredCastellResponse]
}

public struct ChatResponse: Codable, Hashable, Sendable {
    public let reply: String
    public let intent: String
    public let performances: [PerformanceResponse]
    public let winnerLabel: String?
    public let warnings: [String]
    public let rulesetVersion: String
    public let needsClarification: Bool

    public init(
        reply: String,
        intent: String,
        performances: [PerformanceResponse],
        winnerLabel: String?,
        warnings: [String],
        rulesetVersion: String,
        needsClarification: Bool
    ) {
        self.reply = reply
        self.intent = intent
        self.performances = performances
        self.winnerLabel = winnerLabel
        self.warnings = warnings
        self.rulesetVersion = rulesetVersion
        self.needsClarification = needsClarification
    }
}
