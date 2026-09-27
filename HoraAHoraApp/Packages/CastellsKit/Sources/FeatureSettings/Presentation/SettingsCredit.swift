import Foundation

/// A source of the app's data in «Fonts i crèdits», with its official page if it has one.
public struct SettingsCredit: Equatable, Sendable {
    public let name: String
    public let detail: String
    public let url: URL?

    public init(name: String, detail: String, url: URL?) {
        self.name = name
        self.detail = detail
        self.url = url
    }
}
