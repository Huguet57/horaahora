import XCTest
@testable import FeatureAgenda

final class AgendaOtherEventsDisclosureStateTests: XCTestCase {
    func testStartsCollapsedWhenTheDayHasMatchingEvents() {
        let state = AgendaOtherEventsDisclosureState(hasMatchingEvents: true)

        XCTAssertFalse(state.isExpanded)
    }

    func testStartsExpandedWhenNoEventMatchesTheFilter() {
        let state = AgendaOtherEventsDisclosureState(hasMatchingEvents: false)

        XCTAssertTrue(state.isExpanded)
    }

    func testToggleChangesVisibility() {
        var state = AgendaOtherEventsDisclosureState(hasMatchingEvents: true)

        state.toggle()

        XCTAssertTrue(state.isExpanded)
    }
}
