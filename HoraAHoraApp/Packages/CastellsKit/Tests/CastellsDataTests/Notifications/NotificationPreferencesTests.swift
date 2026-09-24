import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class NotificationPreferencesTests: XCTestCase {
    func testNewUsersDefaultToHighAndExistingEnabledUsersKeepLow() {
        let defaults = UserDefaults(suiteName: UUID().uuidString)!
        let newStore = NotificationPreferenceStore(userDefaults: defaults, key: "new")
        XCTAssertEqual(newStore.resolve(existingNotificationsEnabled: false), .high)
        let oldStore = NotificationPreferenceStore(userDefaults: defaults, key: "old")
        XCTAssertEqual(oldStore.resolve(existingNotificationsEnabled: true), .low)
        oldStore.save(.medium)
        let restored = NotificationPreferenceStore(userDefaults: defaults, key: "old")
        XCTAssertEqual(restored.resolve(existingNotificationsEnabled: true), .medium)
    }

    func testSelectionNormalizesAndSerializesStableKeys() throws {
        let selection = NotificationGroupSelection(mode: .custom, keys: [" Minyons ", "MINYONS"])
        XCTAssertEqual(selection.keys, ["minyons"])
        let all = NotificationGroupSelection(mode: .all, keys: ["Minyons"])
        XCTAssertEqual(all.keys, [])
    }
}
