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

/// The settings of the internal app's own sections: the news notifications, their onboarding
/// in Hora a Hora, and the secret gesture that shows or hides Hora a Hora and Agenda.
@MainActor
@Observable
public final class InternalSettingsModel {
    public private(set) var notificationStatus: HourByHourNotificationStatus = .loading
    public private(set) var isUpdatingNotifications = false
    public private(set) var notificationErrorMessage: String?
    public private(set) var isNotificationOnboardingDismissed: Bool
    public private(set) var minimumInterest: NotificationInterestLevel = .high
    public private(set) var isNotificationSynchronizationPending = false
    /// Hora a Hora, Agenda and their settings, hidden unless a secret gesture shows them.
    public private(set) var showsHiddenSections: Bool

    private let notificationManager: any HourByHourNotificationManaging
    private let persistNotificationOnboardingDismissal: @MainActor (Bool) -> Void
    private let hiddenSections: (any HiddenSectionsPreferences)?
    private let now: @MainActor () -> Date
    private var secretTaps = SecretTapSequence()

    public init(
        notificationManager: any HourByHourNotificationManaging,
        notificationOnboardingDismissed: Bool = false,
        persistNotificationOnboardingDismissal: @escaping @MainActor (Bool) -> Void = { _ in },
        hiddenSections: (any HiddenSectionsPreferences)? = nil,
        now: @escaping @MainActor () -> Date = { .now }
    ) {
        self.notificationManager = notificationManager
        isNotificationOnboardingDismissed = notificationOnboardingDismissed
        self.persistNotificationOnboardingDismissal = persistNotificationOnboardingDismissal
        self.hiddenSections = hiddenSections
        showsHiddenSections = hiddenSections?.isUnlocked ?? false
        self.now = now
    }

    public var showsNotificationOnboarding: Bool {
        notificationStatus == .notDetermined && !isNotificationOnboardingDismissed
    }

    public func refreshNotificationStatus() async {
        notificationStatus = await notificationManager.currentStatus()
        if let hiddenSections {
            hiddenSections.resolveDefault(notificationsEnabled: notificationStatus == .enabled)
            showsHiddenSections = hiddenSections.isUnlocked
        }
        await refreshPreferences()
    }

    /// Counts a tap on the version; the seventh quick one shows or hides the hidden sections.
    /// Returns whether this tap changed them.
    @discardableResult
    public func registerSecretTap() -> Bool {
        guard let hiddenSections, secretTaps.register(at: now()) else { return false }
        hiddenSections.setUnlocked(!hiddenSections.isUnlocked)
        showsHiddenSections = hiddenSections.isUnlocked
        return true
    }

    /// Counts a tap on the version row. When the tap completes the secret gesture, returns what
    /// the row says for a moment; nil otherwise.
    public func versionTapMessage() -> String? {
        guard registerSecretTap() else { return nil }
        return showsHiddenSections
            ? "S'han activat Hora a Hora i Agenda"
            : "S'han amagat Hora a Hora i Agenda"
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
