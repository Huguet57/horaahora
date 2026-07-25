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

    func testProjectionUsesNormalizedGroupIndexesToPartitionTheDayAndMonth() {
        var window = AgendaEventWindow()
        window.replace(
            from: agendaDate("2026-07-01"),
            through: agendaDate("2026-08-31"),
            with: [
                makeAgendaEvent(
                    id: "selected-day",
                    localDate: "2026-07-25",
                    title: "Selected day",
                    participatingGroups: ["Castellers de la Vila de Gràcia"]
                ),
                makeAgendaEvent(
                    id: "other-day",
                    localDate: "2026-07-25",
                    title: "Other day",
                    participatingGroups: ["Colla B"]
                ),
                makeAgendaEvent(
                    id: "without-groups",
                    localDate: "2026-07-25",
                    title: "Without groups",
                    participatingGroups: []
                ),
                makeAgendaEvent(
                    id: "selected-month",
                    localDate: "2026-07-26",
                    title: "Selected month",
                    participatingGroups: ["Castellers de la Vila de Gràcia"]
                ),
                makeAgendaEvent(
                    id: "selected-next-month",
                    localDate: "2026-08-01",
                    title: "Selected next month",
                    participatingGroups: ["Castellers de la Vila de Gràcia"]
                ),
            ]
        )
        let selectedKeys = Set(["castellers de la vila de gracia"])

        let projection = window.projection(
            on: agendaDate("2026-07-25"),
            inMonthContaining: agendaDate("2026-07-15")
        ) { participatingGroupKeys in
            !participatingGroupKeys.isDisjoint(with: selectedKeys)
        }

        XCTAssertEqual(projection.events.map(\.externalID), ["selected-day"])
        XCTAssertEqual(
            projection.otherEvents.map(\.externalID),
            ["other-day", "without-groups"]
        )
        XCTAssertEqual(
            projection.eventDateKeys,
            ["2026-07-25", "2026-07-26", "2026-08-01"]
        )
        XCTAssertEqual(
            projection.monthEvents.map(\.externalID),
            ["selected-day", "selected-month"]
        )
    }

    func testProjectionIncludesDatesWithNoGroupsWhenEveryEventMatches() {
        var window = AgendaEventWindow()
        window.replace(
            from: agendaDate("2026-07-01"),
            through: agendaDate("2026-07-31"),
            with: [
                makeAgendaEvent(
                    id: "without-groups",
                    localDate: "2026-07-27",
                    title: "Without groups",
                    participatingGroups: []
                )
            ]
        )

        let projection = window.projection(
            on: agendaDate("2026-07-27"),
            inMonthContaining: agendaDate("2026-07-15"),
            matchingGroupKeys: { _ in true }
        )

        XCTAssertEqual(projection.events.map(\.externalID), ["without-groups"])
        XCTAssertTrue(projection.otherEvents.isEmpty)
        XCTAssertEqual(projection.eventDateKeys, ["2026-07-27"])
        XCTAssertEqual(projection.monthEvents.map(\.externalID), ["without-groups"])
    }
}
