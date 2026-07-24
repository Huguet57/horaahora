import Foundation
import XCTest
@testable import FeatureAgenda

final class AgendaCalendarFoldTests: XCTestCase {
    // MARK: - Week rows (4, 5 and 6-week months)

    func testMonthWeekRowsCoverFourFiveAndSixWeekMonths() {
        let february2027 = AgendaCalendarMath.monthWeekRows(containing: date("2027-02-11"))
        XCTAssertEqual(february2027.count, 4)
        XCTAssertTrue(february2027.allSatisfy { $0.count == 7 })
        XCTAssertEqual(localDate(february2027.first!.first!), "2027-02-01")
        XCTAssertEqual(localDate(february2027.last!.last!), "2027-02-28")

        let july2026 = AgendaCalendarMath.monthWeekRows(containing: date("2026-07-21"))
        XCTAssertEqual(july2026.count, 5)
        XCTAssertTrue(july2026.allSatisfy { $0.count == 7 })
        XCTAssertEqual(localDate(july2026.first!.first!), "2026-06-29")
        XCTAssertEqual(localDate(july2026.last!.last!), "2026-08-02")

        let august2026 = AgendaCalendarMath.monthWeekRows(containing: date("2026-08-15"))
        XCTAssertEqual(august2026.count, 6)
        XCTAssertTrue(august2026.allSatisfy { $0.count == 7 })
        XCTAssertEqual(localDate(august2026.first!.first!), "2026-07-27")
        XCTAssertEqual(localDate(august2026.last!.last!), "2026-09-06")
    }

    func testWeekRowIndexFindsTheRowOfTheSelectedDayIncludingAdjacentMonthDays() {
        let july2026 = AgendaCalendarMath.monthWeekRows(containing: date("2026-07-21"))

        XCTAssertEqual(AgendaCalendarMath.weekRowIndex(of: date("2026-07-21"), in: july2026), 3)
        XCTAssertEqual(AgendaCalendarMath.weekRowIndex(of: date("2026-07-06"), in: july2026), 1)
        // Adjacent-month days that complete the first and last weeks still match.
        XCTAssertEqual(AgendaCalendarMath.weekRowIndex(of: date("2026-06-30"), in: july2026), 0)
        XCTAssertEqual(AgendaCalendarMath.weekRowIndex(of: date("2026-08-01"), in: july2026), 4)
        // A day outside the displayed grid has no active row.
        XCTAssertNil(AgendaCalendarMath.weekRowIndex(of: date("2026-12-21"), in: july2026))
    }

    // MARK: - Fold geometry

    func testFoldDistanceAndGridHeightsForFourFiveAndSixWeekMonths() {
        XCTAssertEqual(AgendaCalendarFold.collapsedGridHeight, 68)

        XCTAssertEqual(AgendaCalendarFold.expandedGridHeight(weekRowCount: 4), 224)
        XCTAssertEqual(AgendaCalendarFold.expandedGridHeight(weekRowCount: 5), 276)
        XCTAssertEqual(AgendaCalendarFold.expandedGridHeight(weekRowCount: 6), 328)

        XCTAssertEqual(AgendaCalendarFold.foldDistance(weekRowCount: 4), 156)
        XCTAssertEqual(AgendaCalendarFold.foldDistance(weekRowCount: 5), 208)
        XCTAssertEqual(AgendaCalendarFold.foldDistance(weekRowCount: 6), 260)
    }

    func testGridHeightInterpolatesBetweenExpandedAndCollapsed() {
        XCTAssertEqual(AgendaCalendarFold.gridHeight(weekRowCount: 5, progress: 0), 276)
        XCTAssertEqual(AgendaCalendarFold.gridHeight(weekRowCount: 5, progress: 1), 68)
        XCTAssertEqual(AgendaCalendarFold.gridHeight(weekRowCount: 5, progress: 0.5), 172)

        XCTAssertEqual(AgendaCalendarFold.inactiveWeekRowSlotHeight(progress: 0), 52)
        XCTAssertEqual(AgendaCalendarFold.inactiveWeekRowSlotHeight(progress: 0.5), 26)
        XCTAssertEqual(AgendaCalendarFold.inactiveWeekRowSlotHeight(progress: 1), 0)
    }

    // MARK: - Progress

    func testProgressIsClampedBetweenZeroAndOne() {
        XCTAssertEqual(AgendaCalendarFold.progress(scrollOffset: -40, foldDistance: 208), 0)
        XCTAssertEqual(AgendaCalendarFold.progress(scrollOffset: 0, foldDistance: 208), 0)
        XCTAssertEqual(
            AgendaCalendarFold.progress(scrollOffset: 104, foldDistance: 208),
            0.5,
            accuracy: 0.0001
        )
        XCTAssertEqual(AgendaCalendarFold.progress(scrollOffset: 208, foldDistance: 208), 1)
        XCTAssertEqual(AgendaCalendarFold.progress(scrollOffset: 600, foldDistance: 208), 1)
        // Degenerate fold distance keeps the calendar expanded instead of dividing by zero.
        XCTAssertEqual(AgendaCalendarFold.progress(scrollOffset: 100, foldDistance: 0), 0)
    }

    func testReduceMotionUsesDirectStateChangesInsteadOfInterpolation() {
        XCTAssertEqual(AgendaCalendarFold.effectiveProgress(0.3, reduceMotion: false), 0.3)
        XCTAssertEqual(AgendaCalendarFold.effectiveProgress(0.3, reduceMotion: true), 0)
        XCTAssertEqual(AgendaCalendarFold.effectiveProgress(0.5, reduceMotion: true), 1)
        XCTAssertEqual(AgendaCalendarFold.effectiveProgress(0.8, reduceMotion: true), 1)
    }

    // MARK: - Snapping

    func testProgressAtOrAboveFiftyPercentSnapsCollapsed() {
        XCTAssertFalse(AgendaCalendarFold.snapsCollapsed(progress: 0))
        XCTAssertFalse(AgendaCalendarFold.snapsCollapsed(progress: 0.499))
        XCTAssertTrue(AgendaCalendarFold.snapsCollapsed(progress: 0.5))
        XCTAssertTrue(AgendaCalendarFold.snapsCollapsed(progress: 1))
    }

    func testSnapTargetOffsetOnlyAdjustsTargetsInsideTheFoldZone() {
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 103, foldDistance: 208), 0)
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 104, foldDistance: 208), 208)
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 207, foldDistance: 208), 208)
        // Outside the fold zone the proposed target is preserved.
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 0, foldDistance: 208), 0)
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: -30, foldDistance: 208), -30)
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 208, foldDistance: 208), 208)
        XCTAssertEqual(AgendaCalendarFold.snapTargetOffset(proposedOffset: 500, foldDistance: 208), 500)
    }

    // MARK: - Content compensation

    func testContentCompensationKeepsCardsGluedToTheCalendarBottom() {
        XCTAssertEqual(AgendaCalendarFold.contentCompensation(progress: 0, foldDistance: 208), 0)
        XCTAssertEqual(AgendaCalendarFold.contentCompensation(progress: 0.5, foldDistance: 208), 104)
        XCTAssertEqual(AgendaCalendarFold.contentCompensation(progress: 1, foldDistance: 208), 208)
    }

    func testContentCompensationMatchesScrollConsumedDuringTheFold() {
        // While folding, the compensation must equal the scroll offset so the cards
        // track the calendar bottom 1:1 without double displacement.
        let foldDistance: CGFloat = 260
        for offset in stride(from: CGFloat(0), through: foldDistance, by: 13) {
            let progress = AgendaCalendarFold.progress(
                scrollOffset: offset,
                foldDistance: foldDistance
            )
            XCTAssertEqual(
                AgendaCalendarFold.contentCompensation(
                    progress: progress,
                    foldDistance: foldDistance
                ),
                offset,
                accuracy: 0.0001
            )
        }
    }

    // MARK: - Minimum fold travel

    func testMinimumListContentHeightGuaranteesTheFullFoldTravel() {
        XCTAssertEqual(
            AgendaCalendarFold.minimumListContentHeight(
                scrollViewHeight: 500,
                remainingFoldDistance: 208
            ),
            708
        )
        XCTAssertEqual(
            AgendaCalendarFold.minimumListContentHeight(
                scrollViewHeight: 500,
                remainingFoldDistance: 0
            ),
            500
        )
        XCTAssertEqual(
            AgendaCalendarFold.minimumListContentHeight(
                scrollViewHeight: 0,
                remainingFoldDistance: 156
            ),
            156
        )
    }

    // MARK: - Helpers

    private func date(_ localDate: String) -> Date {
        let formatter = DateFormatter()
        formatter.calendar = AgendaCalendarMath.calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = AgendaCalendarMath.calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: localDate)!
    }

    private func localDate(_ date: Date) -> String {
        AgendaCalendarMath.localDateKey(date)
    }
}
