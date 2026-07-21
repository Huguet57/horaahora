import UIKit
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    static var shared: AppDelegate?
    static let deepLinkURLKey = "url"
    var deviceToken: String = ""
    var onTokenUpdate: ((String) -> Void)?
    private(set) var pendingDeepLinkURL: URL?

    func consumePendingDeepLinkURL() -> URL? {
        defer { pendingDeepLinkURL = nil }
        return pendingDeepLinkURL
    }

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        AppDelegate.shared = self
        UNUserNotificationCenter.current().delegate = self

        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
            if granted {
                DispatchQueue.main.async {
                    application.registerForRemoteNotifications()
                }
            }
        }
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
        self.deviceToken = "Error: \(error.localizedDescription)"
        DispatchQueue.main.async {
            self.onTokenUpdate?(self.deviceToken)
        }
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
