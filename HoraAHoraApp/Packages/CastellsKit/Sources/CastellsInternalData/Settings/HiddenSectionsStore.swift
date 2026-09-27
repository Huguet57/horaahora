import Foundation
import CastellsDomain

@MainActor
public final class HiddenSectionsStore: HiddenSectionsPreferences {
    private let key = "castells.hidden-sections.unlocked"
    private let userDefaults: UserDefaults

    public init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
    }

    public var isUnlocked: Bool {
        userDefaults.bool(forKey: key)
    }

    public func setUnlocked(_ unlocked: Bool) {
        userDefaults.set(unlocked, forKey: key)
    }

    public func resolveDefault(notificationsEnabled: Bool) {
        guard userDefaults.object(forKey: key) == nil else { return }
        userDefaults.set(notificationsEnabled, forKey: key)
    }
}
