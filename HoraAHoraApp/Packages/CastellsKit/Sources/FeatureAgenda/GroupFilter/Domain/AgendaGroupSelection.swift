import Foundation

public enum AgendaGroupSelection: Codable, Equatable, Sendable {
    case all
    case custom(Set<String>)
}
