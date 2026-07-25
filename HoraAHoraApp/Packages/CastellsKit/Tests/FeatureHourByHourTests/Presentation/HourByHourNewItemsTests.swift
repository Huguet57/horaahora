import XCTest
@testable import FeatureHourByHour

@MainActor
final class HourByHourNewItemsTests: XCTestCase {
    func testRevalidationRevisesNewItemsOnlyForAnUnknownIdentity() async {
        let repository = SequencedHourByHourRepository(pages: [
            page(items: [item("first", title: "Original")]),
            page(items: [item("first", title: "Original")]),
            page(items: [item("first", title: "Actualitzat")]),
            page(items: [item("second"), item("first", title: "Actualitzat")]),
        ])
        let model = HourByHourViewModel(repository: repository)

        await model.loadIfNeeded()
        XCTAssertEqual(model.newItemsRevision, 0)

        await model.revalidate()
        XCTAssertEqual(model.newItemsRevision, 0)

        await model.revalidate()
        XCTAssertEqual(model.newItemsRevision, 0)

        await model.revalidate()
        XCTAssertEqual(model.newItemsRevision, 1)
    }

    func testPaginationDoesNotReviseNewItems() async {
        let repository = SequencedHourByHourRepository(pages: [
            page(items: [item("first")], nextCursor: "page-2"),
            page(items: [item("older")]),
        ])
        let model = HourByHourViewModel(repository: repository)

        await model.loadIfNeeded()
        await model.loadNextIfNeeded(after: model.items.last!)

        XCTAssertEqual(model.newItemsRevision, 0)
    }
}
