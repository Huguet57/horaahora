import XCTest
@testable import FeatureHourByHour

final class HourByHourItemMergerTests: XCTestCase {
    func testRevalidationUpdatesKnownItemsAndPreservesPaginatedItems() {
        let existing = [
            item("first", title: "Original"),
            item("paginated"),
        ]

        let result = HourByHourItemMerger.merge(
            [item("first", title: "Actualitzat")],
            into: existing,
            policy: .revalidate
        )

        XCTAssertEqual(result.items.map(\.id), ["first", "paginated"])
        XCTAssertEqual(result.items.first?.title, "Actualitzat")
        XCTAssertFalse(result.containsNewItems)
    }

    func testRevalidationSignalsAnIdentityThatWasNotPreviouslyLoaded() {
        let result = HourByHourItemMerger.merge(
            [item("second"), item("first")],
            into: [item("first")],
            policy: .revalidate
        )

        XCTAssertEqual(result.items.map(\.id), ["second", "first"])
        XCTAssertTrue(result.containsNewItems)
    }

    func testPaginationAppendsWithoutSignallingNewContent() {
        let result = HourByHourItemMerger.merge(
            [item("older")],
            into: [item("first")],
            policy: .append
        )

        XCTAssertEqual(result.items.map(\.id), ["first", "older"])
        XCTAssertFalse(result.containsNewItems)
    }

    func testIdentityComponentsCannotCollideThroughTheirSeparator() {
        let existing = [
            item("existing", sourceID: "source:part", externalID: "entry"),
        ]
        let incoming = [
            item("incoming", sourceID: "source", externalID: "part:entry"),
        ]

        let result = HourByHourItemMerger.merge(
            incoming,
            into: existing,
            policy: .revalidate
        )

        XCTAssertEqual(result.items.map(\.id), ["incoming", "existing"])
        XCTAssertTrue(result.containsNewItems)
    }
}
