import XCTest
@testable import CastellsData

final class PushSubscriptionTests: XCTestCase {
    func testEnablingWaitsForTheAPNsTokenAndThenRegistersIt() async {
        let remote = PushRemoteStub()
        let coordinator = PushSubscriptionCoordinator(
            remoteService: remote,
            installationID: "installation-1",
            appVersion: "1.0 (3)",
            locale: "ca-ES",
            environment: "development"
        )

        await coordinator.setEnabled(true)
        let countBeforeToken = await remote.registrationCount()
        XCTAssertEqual(countBeforeToken, 0)

        await coordinator.didReceiveDeviceToken("ab12")

        let registrations = await remote.registrationsSnapshot()
        XCTAssertEqual(registrations.count, 1)
        XCTAssertEqual(registrations.first?.installationID, "installation-1")
        XCTAssertEqual(registrations.first?.deviceToken, "ab12")
        XCTAssertEqual(registrations.first?.appVersion, "1.0 (3)")
        XCTAssertEqual(registrations.first?.locale, "ca-ES")
        XCTAssertEqual(registrations.first?.environment, "development")
    }

    func testTokenRotationRegistersTheNewTokenOnlyOnce() async {
        let remote = PushRemoteStub()
        let coordinator = PushSubscriptionCoordinator(
            remoteService: remote,
            installationID: "installation-1",
            appVersion: "1.0 (3)",
            locale: "ca-ES",
            environment: "development"
        )
        await coordinator.setEnabled(true)

        await coordinator.didReceiveDeviceToken("first")
        await coordinator.didReceiveDeviceToken("second")
        await coordinator.didReceiveDeviceToken("second")

        let registrations = await remote.registrationsSnapshot()
        XCTAssertEqual(registrations.map(\.deviceToken), ["first", "second"])
    }

    func testDisablingUnregistersAndAFailureIsRetriedOnNextSynchronization() async {
        let remote = PushRemoteStub(unregisterFailures: 1)
        let coordinator = PushSubscriptionCoordinator(
            remoteService: remote,
            installationID: "installation-1",
            appVersion: "1.0 (3)",
            locale: "ca-ES",
            environment: "development"
        )

        await coordinator.setEnabled(false)
        await coordinator.setEnabled(false)
        await coordinator.setEnabled(false)

        let unregisterCount = await remote.unregisterCount()
        XCTAssertEqual(unregisterCount, 2)
    }
}

private actor PushRemoteStub: PushSubscriptionRemoteService {
    private var registrations: [PushSubscriptionRequest] = []
    private var unregistrations = 0
    private var remainingUnregisterFailures: Int

    init(unregisterFailures: Int = 0) {
        remainingUnregisterFailures = unregisterFailures
    }

    func register(request: PushSubscriptionRequest) async throws {
        registrations.append(request)
    }

    func unregister(installationID: String, environment: String) async throws {
        unregistrations += 1
        if remainingUnregisterFailures > 0 {
            remainingUnregisterFailures -= 1
            throw URLError(.notConnectedToInternet)
        }
    }

    func registrationsSnapshot() -> [PushSubscriptionRequest] {
        registrations
    }

    func registrationCount() -> Int {
        registrations.count
    }

    func unregisterCount() -> Int {
        unregistrations
    }
}
