import UIKit
import UserNotifications
import CastellsData
import CastellsDomain
import FeatureSettings

@MainActor
final class IOSHourByHourNotificationManager: HourByHourNotificationManaging {
    private enum Preference {
        static let enabledKey = "castells.hour-by-hour.notifications-enabled"
    }

    private let notificationCenter: UNUserNotificationCenter
    private let userDefaults: UserDefaults
    private let pushSubscriptionCoordinator: PushSubscriptionCoordinator
    private let preferenceStore: NotificationPreferenceStore
    private let groupSelection: @MainActor () -> NotificationGroupSelection

    var minimumInterest: NotificationInterestLevel { preferenceStore.savedValue ?? .high }

    init(
        notificationCenter: UNUserNotificationCenter = .current(),
        userDefaults: UserDefaults = .standard,
        pushSubscriptionCoordinator: PushSubscriptionCoordinator,
        preferenceStore: NotificationPreferenceStore,
        groupSelection: @escaping @MainActor () -> NotificationGroupSelection
    ) {
        self.notificationCenter = notificationCenter
        self.userDefaults = userDefaults
        self.pushSubscriptionCoordinator = pushSubscriptionCoordinator
        self.preferenceStore = preferenceStore
        self.groupSelection = groupSelection
    }

    func currentStatus() async -> HourByHourNotificationStatus {
        let authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus
        let status = status(for: authorizationStatus)
        preferenceStore.resolve(existingNotificationsEnabled: status == .enabled)

        if status == .enabled {
            await synchronizePreferences()
            await pushSubscriptionCoordinator.setEnabled(true)
            UIApplication.shared.registerForRemoteNotifications()
        } else if status == .disabled || status == .denied {
            await pushSubscriptionCoordinator.setEnabled(false)
        }
        return status
    }

    func enable() async throws -> HourByHourNotificationStatus {
        preferenceStore.resolve(existingNotificationsEnabled: false)
        var authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus

        if authorizationStatus == .notDetermined {
            let granted = try await notificationCenter.requestAuthorization(
                options: [.alert, .badge]
            )
            authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus
            if !granted {
                // If the user later enables the system permission, honour that explicit choice.
                userDefaults.removeObject(forKey: Preference.enabledKey)
                return .denied
            }
        }

        guard authorizationStatus != .denied else { return .denied }

        userDefaults.set(true, forKey: Preference.enabledKey)
        await synchronizePreferences()
        await pushSubscriptionCoordinator.setEnabled(true)
        UIApplication.shared.registerForRemoteNotifications()
        return .enabled
    }

    func disable() async throws -> HourByHourNotificationStatus {
        userDefaults.set(false, forKey: Preference.enabledKey)
        UIApplication.shared.unregisterForRemoteNotifications()
        await pushSubscriptionCoordinator.setEnabled(false)

        let authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus
        return authorizationStatus == .denied ? .denied : .disabled
    }

    func openSystemSettings() async {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        await UIApplication.shared.open(url)
    }

    func setMinimumInterest(_ value: NotificationInterestLevel) async {
        preferenceStore.save(value)
        await synchronizePreferences()
    }

    func synchronizePreferences() async {
        await pushSubscriptionCoordinator.setPreferences(
            minimumInterest: minimumInterest, groupSelection: groupSelection()
        )
    }

    func synchronizationPending() async -> Bool {
        await pushSubscriptionCoordinator.isSynchronizationPending
    }

    private func status(for authorizationStatus: UNAuthorizationStatus) -> HourByHourNotificationStatus {
        switch authorizationStatus {
        case .notDetermined:
            .notDetermined
        case .denied:
            .denied
        case .authorized, .provisional, .ephemeral:
            notificationsEnabledPreference ? .enabled : .disabled
        @unknown default:
            .disabled
        }
    }

    private var notificationsEnabledPreference: Bool {
        guard userDefaults.object(forKey: Preference.enabledKey) != nil else {
            // Preserve the behaviour for users who had already accepted the old launch-time prompt.
            return true
        }
        return userDefaults.bool(forKey: Preference.enabledKey)
    }
}
