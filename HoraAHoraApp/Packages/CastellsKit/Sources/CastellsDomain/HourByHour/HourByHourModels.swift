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
    public let actionURL: URL?
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
        actionURL: URL?,
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

    public var associatedURL: URL? {
        guard let actionURL, actionURL != articleURL else { return nil }
        return actionURL
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
