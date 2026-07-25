import Foundation
import XCTest
import CastellsDomain
@testable import FeatureAgenda

final class AgendaEventWindowTests: XCTestCase {
    func testReplacingARangeDeduplicatesSortsAndPreservesNeighboringEvents() {
        var window = AgendaEventWindow()
        window.replace(
            from: agendaDate("2026-06-01"),
            through: agendaDate("2026-08-31"),
            with: [
                makeAgendaEvent(id: "august", localDate: "2026-08-01", title: "August"),
                makeAgendaEvent(id: "july", localDate: "2026-07-21", title: "July"),
                makeAgendaEvent(id: "july", localDate: "2026-07-21", title: "Duplicate"),
            ]
        )

        window.replace(
            from: agendaDate("2026-07-01"),
            through: agendaDate("2026-07-31"),
            with: [makeAgendaEvent(id: "updated", localDate: "2026-07-22", title: "Updated")]
        )

        XCTAssertEqual(window.dateKeys, ["2026-07-22", "2026-08-01"])
        XCTAssertEqual(
            window.events(on: agendaDate("2026-07-22")).map(\.externalID),
            ["updated"]
        )
    }

    func testEventsInMonthExcludePrefetchedNeighboringMonths() {
        var window = AgendaEventWindow()
        window.replace(
            from: agendaDate("2026-06-01"),
            through: agendaDate("2026-08-31"),
            with: [
                makeAgendaEvent(id: "june", localDate: "2026-06-30", title: "June"),
                makeAgendaEvent(id: "july", localDate: "2026-07-21", title: "July"),
                makeAgendaEvent(id: "august", localDate: "2026-08-01", title: "August"),
            ]
        )

        XCTAssertEqual(
            window.events(inMonthContaining: agendaDate("2026-07-15")).map(\.externalID),
            ["july"]
        )
    }

    func testLoadedMonthsAreTrackedIndependentlyFromTheirEvents() {
        var window = AgendaEventWindow()

        window.markLoaded(from: agendaDate("2026-06-01"), through: agendaDate("2026-08-31"))

        XCTAssertTrue(window.containsMonth(agendaDate("2026-06-15")))
        XCTAssertTrue(window.containsMonth(agendaDate("2026-07-15")))
        XCTAssertTrue(window.containsMonth(agendaDate("2026-08-15")))
        XCTAssertFalse(window.containsMonth(agendaDate("2026-09-15")))
        XCTAssertTrue(window.isEmpty)
    }
}
