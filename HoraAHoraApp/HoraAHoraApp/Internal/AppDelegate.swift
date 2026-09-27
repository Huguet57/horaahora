import UIKit
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    static var shared: AppDelegate?
    static let deepLinkURLKey = "url"
    private(set) var deviceToken: String?
    private var onTokenUpdate: ((String) -> Void)?
    private(set) var pendingDeepLinkURL: URL?

    func consumePendingDeepLinkURL() -> URL? {
        defer { pendingDeepLinkURL = nil }
        return pendingDeepLinkURL
    }

    func setTokenUpdateHandler(_ handler: @escaping (String) -> Void) {
        onTokenUpdate = handler
        if let deviceToken {
            handler(deviceToken)
        }
    }

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        AppDelegate.shared = self
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        self.deviceToken = token
        DispatchQueue.main.async {
            self.onTokenUpdate?(token)
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        // A later foreground refresh asks APNs for a fresh token again.
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .badge, .sound])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        if let urlString = userInfo[Self.deepLinkURLKey] as? String,
           let url = URL(string: urlString) {
            DispatchQueue.main.async {
                self.pendingDeepLinkURL = url
                NotificationCenter.default.post(
                    name: .hourByHourDeepLink,
                    object: nil,
                    userInfo: [Self.deepLinkURLKey: url]
                )
            }
        }
        completionHandler()
    }
}

extension Notification.Name {
    static let hourByHourDeepLink = Notification.Name("castells.hour-by-hour.deep-link")
}
