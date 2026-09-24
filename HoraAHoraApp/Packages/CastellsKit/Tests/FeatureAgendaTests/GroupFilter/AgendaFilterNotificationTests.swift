import XCTest
@testable import FeatureAgenda

@MainActor
final class AgendaFilterNotificationTests: XCTestCase {
    func testOnlyFollowingChangesNotifyTheBridge() {
        let defaults = UserDefaults(suiteName: UUID().uuidString)!
        let store = AgendaUserDefaultsStore(userDefaults: defaults)
        var changes: [AgendaGroupSelection] = []
        store.onSelectionChange = { changes.append($0) }
        var state = store.load()
        state.featuredGroupKeys = ["a"]
        store.save(state)
        XCTAssertTrue(changes.isEmpty)
        state.selection = .custom(["a"])
        store.save(state)
        store.save(state)
        XCTAssertEqual(changes, [.custom(["a"])])
        state.selection = .all
        store.save(state)
        XCTAssertEqual(changes, [.custom(["a"]), .all])
    }
}
