import Foundation

/// Pure math for the progressive fold of the monthly calendar driven by the
/// agenda list scroll. Scroll offset `0...foldDistance` maps to a normalized
/// progress `0...1`; releasing at 50% or more snaps collapsed.
enum AgendaCalendarFold {
    static let weekdayHeaderHeight: CGFloat = 16
    static let weekRowHeight: CGFloat = 44
    static let weekRowSpacing: CGFloat = 8
    /// Vertical slot of one week row: the 8pt gap above it plus the 44pt row.
    static let weekRowSlotHeight: CGFloat = weekRowSpacing + weekRowHeight
    /// Weekday header plus the single remaining (active) week row.
    static let collapsedGridHeight: CGFloat = weekdayHeaderHeight + weekRowSlotHeight

    static func expandedGridHeight(weekRowCount: Int) -> CGFloat {
        weekdayHeaderHeight + CGFloat(max(weekRowCount, 1)) * weekRowSlotHeight
    }

    static func foldDistance(weekRowCount: Int) -> CGFloat {
        expandedGridHeight(weekRowCount: weekRowCount) - collapsedGridHeight
    }

    static func gridHeight(weekRowCount: Int, progress: CGFloat) -> CGFloat {
        expandedGridHeight(weekRowCount: weekRowCount)
            - foldDistance(weekRowCount: weekRowCount) * clamped(progress)
    }

    static func inactiveWeekRowSlotHeight(progress: CGFloat) -> CGFloat {
        weekRowSlotHeight * (1 - clamped(progress))
    }

    static func progress(scrollOffset: CGFloat, foldDistance: CGFloat) -> CGFloat {
        guard foldDistance > 0 else { return 0 }
        return clamped(scrollOffset / foldDistance)
    }

    /// With Reduce Motion the calendar never interpolates: it switches state
    /// directly when the raw progress crosses the snap threshold.
    static func effectiveProgress(_ progress: CGFloat, reduceMotion: Bool) -> CGFloat {
        guard reduceMotion else { return clamped(progress) }
        return snapsCollapsed(progress: progress) ? 1 : 0
    }

    static func snapsCollapsed(progress: CGFloat) -> Bool {
        progress >= 0.5
    }

    /// Adjusts a proposed scroll resting offset so the calendar never settles
    /// half-folded. Targets outside the fold zone are preserved.
    static func snapTargetOffset(proposedOffset: CGFloat, foldDistance: CGFloat) -> CGFloat {
        guard proposedOffset > 0, proposedOffset < foldDistance else { return proposedOffset }
        let foldProgress = progress(scrollOffset: proposedOffset, foldDistance: foldDistance)
        return snapsCollapsed(progress: foldProgress) ? foldDistance : 0
    }

    /// How far the list content must shift down so the cards keep tracking the
    /// calendar bottom while the fold consumes scroll travel.
    static func contentCompensation(progress: CGFloat, foldDistance: CGFloat) -> CGFloat {
        max(foldDistance, 0) * clamped(progress)
    }

    /// Minimum height of the scrollable list content so the full fold travel is
    /// reachable even on days with a single event or no content at all.
    static func minimumListContentHeight(
        scrollViewHeight: CGFloat,
        remainingFoldDistance: CGFloat
    ) -> CGFloat {
        max(scrollViewHeight, 0) + max(remainingFoldDistance, 0)
    }

    private static func clamped(_ value: CGFloat) -> CGFloat {
        min(max(value, 0), 1)
    }
}
