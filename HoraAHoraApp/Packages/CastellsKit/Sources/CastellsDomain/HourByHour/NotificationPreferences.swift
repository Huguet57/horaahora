import Foundation

public enum NotificationInterestLevel: String, Codable, CaseIterable, Sendable {
    case low, medium, high
}

public struct NotificationGroupSelection: Codable, Equatable, Sendable {
    public enum Mode: String, Codable, Sendable { case all, custom }
    public let mode: Mode
    public let keys: [String]

    public init(mode: Mode = .all, keys: [String] = []) {
        self.mode = mode
        self.keys = mode == .all ? [] : Set(keys.map(GroupNameKey.normalize).filter { !$0.isEmpty }).sorted()
    }
}
