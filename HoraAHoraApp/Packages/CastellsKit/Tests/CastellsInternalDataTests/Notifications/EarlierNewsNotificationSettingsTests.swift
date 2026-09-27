import Foundation
import XCTest
import CastellsData
@testable import CastellsInternalData

/// The public app retires the news notifications of earlier versions when it finds one of the
/// settings they wrote. These stores still write them, in the internal app.
@MainActor
final class EarlierNewsNotificationSettingsTests: XCTestCase {
    func testThePublicAppRecognizesEverySettingTheseStoresWrite() async {
        let writes: [@MainActor (UserDefaults) -> Void] = [
            { NotificationPreferenceStore(userDefaults: $0).save(.high) },
            { HiddenSectionsStore(userDefaults: $0).setUnlocked(false) },
        ]

        for write in writes {
            let defaults = UserDefaults(suiteName: UUID().uuidString)!
            write(defaults)
            let remote = CountingRemote()
            let retirement = LegacyNewsNotificationsRetirement(
                userDefaults: defaults,
                remoteService: remote,
                installationID: "installation-1",
                environment: "production",
                system: NoNotificationPermission()
            )

            await retirement.retireIfNeeded()

            let counts = await remote.counts()
            XCTAssertEqual(counts.registrations, 0)
            XCTAssertEqual(counts.unregistrations, 1)
        }
    }
}

private actor CountingRemote: PushSubscriptionRemoteService {
    private var registrations = 0
    private var unregistrations = 0

    func register(request: PushSubscriptionRequest) async throws {
        registrations += 1
    }

    func unregister(installationID: String, environment: String) async throws {
        unregistrations += 1
    }

    func counts() -> (registrations: Int, unregistrations: Int) {
        (registrations, unregistrations)
    }
}

@MainActor
private final class NoNotificationPermission: LegacyNewsNotificationsSystem {
    func hadNewsNotifications() async -> Bool { false }

    func stopShowingNewsNotifications() {}
}
