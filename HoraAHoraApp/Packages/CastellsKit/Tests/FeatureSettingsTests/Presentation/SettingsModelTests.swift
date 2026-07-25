import XCTest
@testable import FeatureSettings

@MainActor
final class SettingsModelTests: XCTestCase {
    func testRefreshExposesPendingPermissionAndShowsOnboarding() async {
        let manager = NotificationManagerStub(initialStatus: .notDetermined)
        let model = SettingsModel(
            notificationManager: manager,
            notificationOnboardingDismissed: false
        )

        await model.refreshNotificationStatus()

        XCTAssertEqual(model.notificationStatus, .notDetermined)
        XCTAssertTrue(model.showsNotificationOnboarding)
        XCTAssertFalse(model.isUpdatingNotifications)
    }

    func testEnablingNotificationsRequestsPermission() async {
        let manager = NotificationManagerStub(
            initialStatus: .notDetermined,
            enabledStatus: .enabled
        )
        let model = SettingsModel(notificationManager: manager)

        await model.setHourByHourNotificationsEnabled(true)

        XCTAssertEqual(manager.enableCallCount, 1)
        XCTAssertEqual(model.notificationStatus, .enabled)
        XCTAssertFalse(model.showsNotificationOnboarding)
    }

    func testDeniedPermissionIsExposedAsBlockedByIOS() async {
        let manager = NotificationManagerStub(
            initialStatus: .notDetermined,
            enabledStatus: .denied
        )
        let model = SettingsModel(notificationManager: manager)

        await model.setHourByHourNotificationsEnabled(true)

        XCTAssertEqual(model.notificationStatus, .denied)
        XCTAssertFalse(model.showsNotificationOnboarding)
    }

    func testDisablingNotificationsUsesTheInjectedPort() async {
        let manager = NotificationManagerStub(
            initialStatus: .enabled,
            disabledStatus: .disabled
        )
        let model = SettingsModel(notificationManager: manager)

        await model.setHourByHourNotificationsEnabled(false)

        XCTAssertEqual(manager.disableCallCount, 1)
        XCTAssertEqual(model.notificationStatus, .disabled)
    }

    func testReturningFromIOSSettingsRefreshesDeniedPermission() async {
        let manager = NotificationManagerStub(initialStatus: .denied)
        let model = SettingsModel(notificationManager: manager)
        await model.refreshNotificationStatus()
        manager.currentStatusValue = .enabled

        await model.refreshNotificationStatus()

        XCTAssertEqual(manager.currentStatusCallCount, 2)
        XCTAssertEqual(model.notificationStatus, .enabled)
    }

    func testOpeningIOSSettingsUsesTheInjectedPort() async {
        let manager = NotificationManagerStub(initialStatus: .denied)
        let model = SettingsModel(notificationManager: manager)

        await model.openSystemSettings()

        XCTAssertEqual(manager.openSystemSettingsCallCount, 1)
    }

    func testOnboardingCanBeDismissedAndPersistsTheChoice() {
        var persistedValue: Bool?
        let model = SettingsModel(
            notificationManager: NotificationManagerStub(initialStatus: .notDetermined),
            notificationOnboardingDismissed: false,
            persistNotificationOnboardingDismissal: { persistedValue = $0 }
        )
        model.setNotificationStatusForTesting(.notDetermined)

        model.handleNotificationOnboarding(.dismiss)

        XCTAssertFalse(model.showsNotificationOnboarding)
        XCTAssertEqual(persistedValue, true)
    }

    func testOnboardingConfigureActionOpensSettingsWithoutDismissingIt() {
        var didOpenSettings = false
        let model = SettingsModel(
            notificationManager: NotificationManagerStub(initialStatus: .notDetermined),
            notificationOnboardingDismissed: false
        )
        model.setNotificationStatusForTesting(.notDetermined)

        model.handleNotificationOnboarding(.configure) {
            didOpenSettings = true
        }

        XCTAssertTrue(didOpenSettings)
        XCTAssertTrue(model.showsNotificationOnboarding)
    }

    func testFailureKeepsPreviousStatusAndShowsError() async {
        let manager = NotificationManagerStub(
            initialStatus: .enabled,
            failure: NotificationManagerStubError.failed
        )
        let model = SettingsModel(notificationManager: manager)
        await model.refreshNotificationStatus()

        await model.setHourByHourNotificationsEnabled(false)

        XCTAssertEqual(model.notificationStatus, .enabled)
        XCTAssertEqual(model.notificationErrorMessage, "No s'ha pogut canviar la configuració.")
        XCTAssertFalse(model.isUpdatingNotifications)
    }
}

@MainActor
private final class NotificationManagerStub: HourByHourNotificationManaging {
    var currentStatusValue: HourByHourNotificationStatus
    var currentStatusCallCount = 0
    var enableCallCount = 0
    var disableCallCount = 0
    var openSystemSettingsCallCount = 0
    private let enabledStatus: HourByHourNotificationStatus
    private let disabledStatus: HourByHourNotificationStatus
    private let failure: (any Error)?

    init(
        initialStatus: HourByHourNotificationStatus,
        enabledStatus: HourByHourNotificationStatus = .enabled,
        disabledStatus: HourByHourNotificationStatus = .disabled,
        failure: (any Error)? = nil
    ) {
        currentStatusValue = initialStatus
        self.enabledStatus = enabledStatus
        self.disabledStatus = disabledStatus
        self.failure = failure
    }

    func currentStatus() async -> HourByHourNotificationStatus {
        currentStatusCallCount += 1
        return currentStatusValue
    }

    func enable() async throws -> HourByHourNotificationStatus {
        enableCallCount += 1
        if let failure { throw failure }
        return enabledStatus
    }

    func disable() async throws -> HourByHourNotificationStatus {
        disableCallCount += 1
        if let failure { throw failure }
        return disabledStatus
    }

    func openSystemSettings() async {
        openSystemSettingsCallCount += 1
    }
}

private enum NotificationManagerStubError: LocalizedError {
    case failed

    var errorDescription: String? {
        "No s'ha pogut canviar la configuració."
    }
}
