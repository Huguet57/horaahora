import Foundation

/// What an earlier version of the app set up in the system for news notifications.
@MainActor
public protocol LegacyNewsNotificationsSystem: AnyObject {
    /// Whether the system still remembers news notifications from an earlier version.
    func hadNewsNotifications() async -> Bool
    /// Stops the system from receiving and showing them, including those already shown.
    func stopShowingNewsNotifications()
}

/// The public app has no news notifications. An installation that used them in an earlier
/// version may still be subscribed on the backend, and the system would keep showing what
/// arrives. This stops both: it removes them from the system and unsubscribes the
/// installation, and tries again at every launch until the backend confirms it. It never
/// subscribes anything, whatever the earlier version's settings say.
@MainActor
public final class LegacyNewsNotificationsRetirement {
    private static let retiredKey = "castells.news-notifications.retired.v1"
    /// Written by the news notifications and the hidden sections of earlier versions.
    private static let earlierKeys = [
        "castells.hour-by-hour.notifications-enabled",
        "castells.hour-by-hour.minimum-interest.v1",
        "castells.hour-by-hour.notification-onboarding-dismissed",
        "castells.hidden-sections.unlocked",
    ]

    private let userDefaults: UserDefaults
    private let remoteService: any PushSubscriptionRemoteService
    private let installationID: String
    private let environment: String
    private let system: any LegacyNewsNotificationsSystem
    private var isRetiring = false

    public init(
        userDefaults: UserDefaults = .standard,
        remoteService: any PushSubscriptionRemoteService,
        installationID: String,
        environment: String,
        system: any LegacyNewsNotificationsSystem
    ) {
        self.userDefaults = userDefaults
        self.remoteService = remoteService
        self.installationID = installationID
        self.environment = environment
        self.system = system
    }

    public func retireIfNeeded() async {
        guard !isRetiring, !userDefaults.bool(forKey: Self.retiredKey) else { return }
        isRetiring = true
        defer { isRetiring = false }

        guard await hadNewsNotifications() else {
            userDefaults.set(true, forKey: Self.retiredKey)
            return
        }
        system.stopShowingNewsNotifications()
        do {
            try await remoteService.unregister(installationID: installationID, environment: environment)
            userDefaults.set(true, forKey: Self.retiredKey)
        } catch {
            // Offline or a server error: the next launch or return to the foreground tries again.
        }
    }

    /// An earlier version with news notifications left one of its settings, or the permission.
    private func hadNewsNotifications() async -> Bool {
        if Self.earlierKeys.contains(where: { userDefaults.object(forKey: $0) != nil }) {
            return true
        }
        return await system.hadNewsNotifications()
    }
}
