import Foundation
import Observation

public enum HourByHourNotificationStatus: Equatable, Sendable {
    case loading
    case notDetermined
    case enabled
    case disabled
    case denied
}

@MainActor
public protocol HourByHourNotificationManaging: AnyObject {
    func currentStatus() async -> HourByHourNotificationStatus
    func enable() async throws -> HourByHourNotificationStatus
    func disable() async throws -> HourByHourNotificationStatus
    func openSystemSettings() async
}

public enum NotificationOnboardingAction: Sendable {
    case configure
    case dismiss
}

@MainActor
@Observable
public final class SettingsModel {
    public private(set) var notificationStatus: HourByHourNotificationStatus = .loading
    public private(set) var isUpdatingNotifications = false
    public private(set) var notificationErrorMessage: String?
    public private(set) var isNotificationOnboardingDismissed: Bool

    private let notificationManager: any HourByHourNotificationManaging
    private let persistNotificationOnboardingDismissal: @MainActor (Bool) -> Void

    public init(
        notificationManager: any HourByHourNotificationManaging,
        notificationOnboardingDismissed: Bool = false,
        persistNotificationOnboardingDismissal: @escaping @MainActor (Bool) -> Void = { _ in }
    ) {
        self.notificationManager = notificationManager
        isNotificationOnboardingDismissed = notificationOnboardingDismissed
        self.persistNotificationOnboardingDismissal = persistNotificationOnboardingDismissal
    }

    public var showsNotificationOnboarding: Bool {
        notificationStatus == .notDetermined && !isNotificationOnboardingDismissed
    }

    public func refreshNotificationStatus() async {
        notificationStatus = await notificationManager.currentStatus()
    }

    public func setHourByHourNotificationsEnabled(_ enabled: Bool) async {
        guard !isUpdatingNotifications else { return }
        isUpdatingNotifications = true
        notificationErrorMessage = nil
        defer { isUpdatingNotifications = false }

        do {
            notificationStatus = try await enabled
                ? notificationManager.enable()
                : notificationManager.disable()
        } catch {
            notificationErrorMessage = error.localizedDescription
        }
    }

    public func openSystemSettings() async {
        await notificationManager.openSystemSettings()
    }

    public func handleNotificationOnboarding(
        _ action: NotificationOnboardingAction,
        openSettings: @MainActor () -> Void = {}
    ) {
        switch action {
        case .configure:
            openSettings()
        case .dismiss:
            isNotificationOnboardingDismissed = true
            persistNotificationOnboardingDismissal(true)
        }
    }

    func setNotificationStatusForTesting(_ status: HourByHourNotificationStatus) {
        notificationStatus = status
    }
}
