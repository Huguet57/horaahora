import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class HiddenSectionsStoreTests: XCTestCase {
    func testNewInstallationsStartWithTheSectionsHidden() {
        let store = HiddenSectionsStore(userDefaults: freshDefaults())

        store.resolveDefault(notificationsEnabled: false)

        XCTAssertFalse(store.isUnlocked)
    }

    func testUsersWhoAlreadyGetNewsNotificationsKeepTheSections() {
        let store = HiddenSectionsStore(userDefaults: freshDefaults())
        XCTAssertFalse(store.isUnlocked)

        store.resolveDefault(notificationsEnabled: true)

        XCTAssertTrue(store.isUnlocked)
    }

    func testOnlyTheFirstKnownNotificationStatusDecidesTheDefault() {
        let store = HiddenSectionsStore(userDefaults: freshDefaults())
        store.resolveDefault(notificationsEnabled: false)

        store.resolveDefault(notificationsEnabled: true)

        XCTAssertFalse(store.isUnlocked)
    }

    func testAnExplicitChoiceWinsOverTheDefault() {
        let store = HiddenSectionsStore(userDefaults: freshDefaults())
        store.setUnlocked(false)

        store.resolveDefault(notificationsEnabled: true)

        XCTAssertFalse(store.isUnlocked)
    }

    func testTheChoicePersistsAcrossLaunches() {
        let defaults = freshDefaults()
        HiddenSectionsStore(userDefaults: defaults).setUnlocked(true)

        XCTAssertTrue(HiddenSectionsStore(userDefaults: defaults).isUnlocked)
    }

    private func freshDefaults() -> UserDefaults {
        UserDefaults(suiteName: UUID().uuidString)!
    }
}
