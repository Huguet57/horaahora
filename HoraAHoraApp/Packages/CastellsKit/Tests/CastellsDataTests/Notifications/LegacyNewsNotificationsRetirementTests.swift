import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class LegacyNewsNotificationsRetirementTests: XCTestCase {
    func testANewInstallationHasNothingToRetire() async {
        let remote = RetirementRemoteStub()
        let system = LegacySystemStub()
        let retirement = makeRetirement(defaults: freshDefaults(), remote: remote, system: system)

        await retirement.retireIfNeeded()
        await retirement.retireIfNeeded()

        let unregistrations = await remote.unregistrationsSnapshot()
        XCTAssertEqual(unregistrations, [])
        XCTAssertEqual(system.stops, 0)
        XCTAssertEqual(system.checks, 1)
    }

    func testAnInstallationThatUsedNewsNotificationsStopsThemOnceAndLeavesTheBackend() async {
        let defaults = freshDefaults()
        defaults.set(true, forKey: "castells.hour-by-hour.notifications-enabled")
        let remote = RetirementRemoteStub()
        let system = LegacySystemStub()
        let retirement = makeRetirement(defaults: defaults, remote: remote, system: system)

        await retirement.retireIfNeeded()
        await retirement.retireIfNeeded()

        let unregistrations = await remote.unregistrationsSnapshot()
        XCTAssertEqual(unregistrations, ["installation-1 production"])
        XCTAssertEqual(system.stops, 1)
    }

    func testTheOldSettingsAndPermissionNeverSubscribeTheDeviceAgain() async {
        let defaults = freshDefaults()
        defaults.set(true, forKey: "castells.hour-by-hour.notifications-enabled")
        NotificationPreferenceStore(userDefaults: defaults).save(.low)
        HiddenSectionsStore(userDefaults: defaults).setUnlocked(true)
        let remote = RetirementRemoteStub()
        let system = LegacySystemStub(hadNewsNotifications: true)

        await makeRetirement(defaults: defaults, remote: remote, system: system).retireIfNeeded()

        let registrations = await remote.registrationCount()
        let unregistrations = await remote.unregistrationsSnapshot()
        XCTAssertEqual(registrations, 0)
        XCTAssertEqual(unregistrations.count, 1)
    }

    func testAFailedUnsubscriptionIsRetriedUntilTheBackendConfirmsIt() async {
        let defaults = freshDefaults()
        defaults.set(true, forKey: "castells.hour-by-hour.notifications-enabled")
        let remote = RetirementRemoteStub(failures: 2)
        let system = LegacySystemStub()
        let retirement = makeRetirement(defaults: defaults, remote: remote, system: system)

        for _ in 0..<4 {
            await retirement.retireIfNeeded()
        }

        let unregistrations = await remote.unregistrationsSnapshot()
        XCTAssertEqual(unregistrations.count, 3)
        XCTAssertEqual(system.stops, 3)
    }

    func testEverySettingThatAnEarlierVersionWroteCounts() async {
        let earlierSettings: [@MainActor (UserDefaults) -> Void] = [
            { NotificationPreferenceStore(userDefaults: $0).save(.high) },
            { HiddenSectionsStore(userDefaults: $0).setUnlocked(false) },
            { $0.set(false, forKey: "castells.hour-by-hour.notifications-enabled") },
            { $0.set(true, forKey: "castells.hour-by-hour.notification-onboarding-dismissed") },
        ]

        for write in earlierSettings {
            let defaults = freshDefaults()
            write(defaults)
            let remote = RetirementRemoteStub()

            await makeRetirement(defaults: defaults, remote: remote, system: LegacySystemStub())
                .retireIfNeeded()

            let unregistrations = await remote.unregistrationsSnapshot()
            XCTAssertEqual(unregistrations.count, 1)
        }
    }

    func testThePermissionAnEarlierVersionAskedForAlsoCounts() async {
        let remote = RetirementRemoteStub()
        let system = LegacySystemStub(hadNewsNotifications: true)

        await makeRetirement(defaults: freshDefaults(), remote: remote, system: system).retireIfNeeded()

        let unregistrations = await remote.unregistrationsSnapshot()
        XCTAssertEqual(unregistrations.count, 1)
        XCTAssertEqual(system.stops, 1)
    }

    private func makeRetirement(
        defaults: UserDefaults,
        remote: RetirementRemoteStub,
        system: LegacySystemStub
    ) -> LegacyNewsNotificationsRetirement {
        LegacyNewsNotificationsRetirement(
            userDefaults: defaults,
            remoteService: remote,
            installationID: "installation-1",
            environment: "production",
            system: system
        )
    }

    private func freshDefaults() -> UserDefaults {
        UserDefaults(suiteName: UUID().uuidString)!
    }
}

private actor RetirementRemoteStub: PushSubscriptionRemoteService {
    private var registrations: [PushSubscriptionRequest] = []
    private var unregistrations: [String] = []
    private var remainingFailures: Int

    init(failures: Int = 0) {
        remainingFailures = failures
    }

    func register(request: PushSubscriptionRequest) async throws {
        registrations.append(request)
    }

    func unregister(installationID: String, environment: String) async throws {
        unregistrations.append("\(installationID) \(environment)")
        if remainingFailures > 0 {
            remainingFailures -= 1
            throw URLError(.notConnectedToInternet)
        }
    }

    func registrationCount() -> Int {
        registrations.count
    }

    func unregistrationsSnapshot() -> [String] {
        unregistrations
    }
}

@MainActor
private final class LegacySystemStub: LegacyNewsNotificationsSystem {
    private let hadNews: Bool
    private(set) var checks = 0
    private(set) var stops = 0

    init(hadNewsNotifications: Bool = false) {
        hadNews = hadNewsNotifications
    }

    func hadNewsNotifications() async -> Bool {
        checks += 1
        return hadNews
    }

    func stopShowingNewsNotifications() {
        stops += 1
    }
}
