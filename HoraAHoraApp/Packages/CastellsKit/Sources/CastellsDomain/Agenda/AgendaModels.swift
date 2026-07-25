import Foundation

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

public struct CastellerGroupDirectory: Codable, Equatable, Sendable {
    public let groups: [String]
    public let revision: String
    public let officialURL: URL

    public init(groups: [String], revision: String, officialURL: URL) {
        self.groups = groups
        self.revision = revision
        self.officialURL = officialURL
    }
}
