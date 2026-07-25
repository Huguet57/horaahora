import Foundation

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
