import UIKit
import UserNotifications
import CastellsData
import FeatureSettings

@MainActor
final class IOSHourByHourNotificationManager: HourByHourNotificationManaging {
    private enum Preference {
        static let enabledKey = "castells.hour-by-hour.notifications-enabled"
    }

    private let notificationCenter: UNUserNotificationCenter
    private let userDefaults: UserDefaults
    private let pushSubscriptionCoordinator: PushSubscriptionCoordinator

    init(
        notificationCenter: UNUserNotificationCenter = .current(),
        userDefaults: UserDefaults = .standard,
        pushSubscriptionCoordinator: PushSubscriptionCoordinator
    ) {
        self.notificationCenter = notificationCenter
        self.userDefaults = userDefaults
        self.pushSubscriptionCoordinator = pushSubscriptionCoordinator
    }

    func currentStatus() async -> HourByHourNotificationStatus {
        let authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus
        let status = status(for: authorizationStatus)

        if status == .enabled {
            await pushSubscriptionCoordinator.setEnabled(true)
            UIApplication.shared.registerForRemoteNotifications()
        } else if status == .disabled {
            await pushSubscriptionCoordinator.setEnabled(false)
        }
        return status
    }

    func enable() async throws -> HourByHourNotificationStatus {
        var authorizationStatus = await notificationCenter.notificationSettings().authorizationStatus

        if authorizationStatus == .notDetermined {
            let granted = try await notificationCenter.requestAuthorization(
                options: [.alert, .badge, .sound]
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
