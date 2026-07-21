import XCTest
@testable import FeatureHourByHour

@MainActor
final class NotificationSettingsModelTests: XCTestCase {
    func testRefreshExposesThatFirstRunStillNeedsSetup() async {
        let manager = NotificationManagerStub(initialStatus: .notDetermined)
        let model = HourByHourNotificationSettingsModel(manager: manager)

        await model.refresh()

        XCTAssertEqual(model.status, .notDetermined)
        XCTAssertFalse(model.isUpdating)
    }

    func testEnablingRequestsPermissionThroughTheManager() async {
        let manager = NotificationManagerStub(
            initialStatus: .notDetermined,
            enabledStatus: .enabled
        )
        let model = HourByHourNotificationSettingsModel(manager: manager)

        await model.setEnabled(true)

        XCTAssertEqual(manager.enableCallCount, 1)
        XCTAssertEqual(model.status, .enabled)
    }

    func testDisablingStopsHourByHourNotifications() async {
        let manager = NotificationManagerStub(
            initialStatus: .enabled,
            disabledStatus: .disabled
        )
        let model = HourByHourNotificationSettingsModel(manager: manager)

        await model.setEnabled(false)

        XCTAssertEqual(manager.disableCallCount, 1)
        XCTAssertEqual(model.status, .disabled)
    }

    func testFailureKeepsThePreviousStatusAndShowsAnError() async {
        let manager = NotificationManagerStub(
            initialStatus: .enabled,
            failure: NotificationManagerStubError.failed
        )
        let model = HourByHourNotificationSettingsModel(manager: manager)
        await model.refresh()

        await model.setEnabled(false)

        XCTAssertEqual(model.status, .enabled)
        XCTAssertEqual(model.errorMessage, "No s'ha pogut canviar la configuració.")
        XCTAssertFalse(model.isUpdating)
    }
}

@MainActor
private final class NotificationManagerStub: HourByHourNotificationManaging {
    var enableCallCount = 0
    var disableCallCount = 0
    private let initialStatus: HourByHourNotificationStatus
    private let enabledStatus: HourByHourNotificationStatus
    private let disabledStatus: HourByHourNotificationStatus
    private let failure: (any Error)?

    init(
        initialStatus: HourByHourNotificationStatus,
        enabledStatus: HourByHourNotificationStatus = .enabled,
        disabledStatus: HourByHourNotificationStatus = .disabled,
        failure: (any Error)? = nil
    ) {
        self.initialStatus = initialStatus
        self.enabledStatus = enabledStatus
        self.disabledStatus = disabledStatus
        self.failure = failure
    }

    func currentStatus() async -> HourByHourNotificationStatus {
        initialStatus
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

    func openSystemSettings() async {}
}

private enum NotificationManagerStubError: LocalizedError {
    case failed

    var errorDescription: String? {
        "No s'ha pogut canviar la configuració."
    }
}
