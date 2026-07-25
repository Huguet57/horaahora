import CoreGraphics
import XCTest
@testable import FeatureAgenda

final class AgendaGroupFilterSheetInteractionTests: XCTestCase {
    func testUpwardVerticalDragRequestsSheetExpansion() {
        XCTAssertTrue(
            AgendaGroupFilterSheetInteraction.requestsExpansion(
                translation: CGSize(width: 2, height: -12)
            )
        )
    }

    func testDownwardAndHorizontalDragsDoNotRequestSheetExpansion() {
        XCTAssertFalse(
            AgendaGroupFilterSheetInteraction.requestsExpansion(
                translation: CGSize(width: 2, height: 12)
            )
        )
        XCTAssertFalse(
            AgendaGroupFilterSheetInteraction.requestsExpansion(
                translation: CGSize(width: 12, height: -2)
            )
        )
    }
}
