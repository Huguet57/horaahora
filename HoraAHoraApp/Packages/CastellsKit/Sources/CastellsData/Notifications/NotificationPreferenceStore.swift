import Foundation
import CastellsDomain

@MainActor
public final class NotificationPreferenceStore {
    private let userDefaults: UserDefaults
    private let key: String

    public init(userDefaults: UserDefaults = .standard,
                key: String = "castells.hour-by-hour.minimum-interest.v1") {
        self.userDefaults = userDefaults
        self.key = key
    }

    public var savedValue: NotificationInterestLevel? {
        userDefaults.string(forKey: key).flatMap(NotificationInterestLevel.init(rawValue:))
    }

    @discardableResult
    public func resolve(existingNotificationsEnabled: Bool) -> NotificationInterestLevel {
        if let savedValue { return savedValue }
        let value: NotificationInterestLevel = existingNotificationsEnabled ? .low : .high
        save(value)
        return value
    }

    public func save(_ value: NotificationInterestLevel) {
        userDefaults.set(value.rawValue, forKey: key)
    }
}
