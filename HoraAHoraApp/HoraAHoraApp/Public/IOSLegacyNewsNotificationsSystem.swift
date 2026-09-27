import UIKit
import UserNotifications
import CastellsData

/// The news notifications that earlier versions set up: the permission they asked for, the APNs
/// registration and what Notification Center still shows. The public app never asks for the
/// permission and never registers.
@MainActor
final class IOSLegacyNewsNotificationsSystem: LegacyNewsNotificationsSystem {
    private let notificationCenter: UNUserNotificationCenter

    init(notificationCenter: UNUserNotificationCenter = .current()) {
        self.notificationCenter = notificationCenter
    }

    func hadNewsNotifications() async -> Bool {
        await notificationCenter.notificationSettings().authorizationStatus != .notDetermined
    }

    func stopShowingNewsNotifications() {
        // Apple's advice for a version that stops supporting remote notifications: the device
        // token stops being valid, so nothing the backend still sends is delivered.
        UIApplication.shared.unregisterForRemoteNotifications()
        notificationCenter.removeAllDeliveredNotifications()
    }
}
