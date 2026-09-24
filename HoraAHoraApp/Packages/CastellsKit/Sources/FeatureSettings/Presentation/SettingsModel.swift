import Foundation
import Observation
import CastellsDomain

public enum HourByHourNotificationStatus: Equatable, Sendable {
    case loading
    case notDetermined
    case enabled
    case disabled
    case denied
}

@MainActor
public protocol HourByHourNotificationManaging: AnyObject {
    var minimumInterest: NotificationInterestLevel { get }
    func setMinimumInterest(_ value: NotificationInterestLevel) async
    func synchronizationPending() async -> Bool
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
    public private(set) var minimumInterest: NotificationInterestLevel = .high
    public private(set) var isNotificationSynchronizationPending = false

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
        await refreshPreferences()
    }

    public func setMinimumInterest(_ value: NotificationInterestLevel) async {
        minimumInterest = value
        await notificationManager.setMinimumInterest(value)
        await refreshPreferences()
    }

    public func setNotificationSynchronizationPending(_ pending: Bool) {
        isNotificationSynchronizationPending = pending
    }

    private func refreshPreferences() async {
        minimumInterest = notificationManager.minimumInterest
        isNotificationSynchronizationPending = await notificationManager.synchronizationPending()
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
            await refreshPreferences()
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
