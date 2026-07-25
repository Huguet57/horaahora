import Foundation

public struct AgendaFilterState: Codable, Equatable, Sendable {
    public var selection: AgendaGroupSelection
    public var featuredGroupKeys: Set<String>
    public var cachedGroups: [String]
    public var directoryRevision: String?

    public init(
        selection: AgendaGroupSelection = .all,
        featuredGroupKeys: Set<String> = [],
        cachedGroups: [String] = [],
        directoryRevision: String? = nil
    ) {
        self.selection = selection
        self.featuredGroupKeys = featuredGroupKeys
        self.cachedGroups = cachedGroups
        self.directoryRevision = directoryRevision
    }
}
