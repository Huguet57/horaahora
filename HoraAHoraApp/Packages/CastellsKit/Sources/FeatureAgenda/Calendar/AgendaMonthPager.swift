import Foundation
import SwiftUI

extension AgendaCalendarView {
    var monthPager: some View {
        GeometryReader { geometry in
            let pageWidth = geometry.size.width
            HStack(alignment: .top, spacing: 0) {
                monthGrid(containing: monthDate(offset: -1))
                    .frame(width: pageWidth)
                monthGrid(containing: visibleMonth)
                    .frame(width: pageWidth)
                monthGrid(containing: monthDate(offset: 1))
                    .frame(width: pageWidth)
            }
            .frame(width: pageWidth * 3, alignment: .leading)
            .offset(x: -pageWidth + monthDragOffset)
            .contentShape(Rectangle())
            .highPriorityGesture(monthPagingGesture(pageWidth: pageWidth))
            .onAppear { monthPageWidth = pageWidth }
            .onChange(of: pageWidth) { _, newWidth in monthPageWidth = newWidth }
        }
        .frame(height: monthPagerHeight)
        .clipped()
    }

    func monthGrid(containing referenceDate: Date) -> some View {
        let rows = AgendaCalendarMath.monthWeekRows(containing: referenceDate)
        let activeRow = AgendaCalendarMath.weekRowIndex(of: visibleWeek, in: rows) ?? 0
        let month = monthStart(containing: referenceDate)

        return VStack(spacing: 0) {
            weekdayHeaderRow

            ForEach(Array(rows.enumerated()), id: \.offset) { index, dates in
                monthWeekRow(dates, in: month, isActive: index == activeRow)
            }
        }
    }

    /// One week of the month grid. The active week keeps its full slot while
    /// the rest shrink and fade with the fold progress.
    func monthWeekRow(_ dates: [Date], in month: Date, isActive: Bool) -> some View {
        let slotHeight = isActive
            ? AgendaCalendarFold.weekRowSlotHeight
            : AgendaCalendarFold.inactiveWeekRowSlotHeight(progress: foldProgress)

        return HStack(spacing: 4) {
            ForEach(dates, id: \.self) { date in
                if calendar.isDate(date, equalTo: month, toGranularity: .month) {
                    dayButton(date)
                } else if isActive {
                    dayButton(date)
                        .opacity(foldProgress)
                        .allowsHitTesting(isCollapsed)
                        .accessibilityHidden(!isCollapsed)
                } else {
                    Color.clear
                        .frame(maxWidth: .infinity)
                }
            }
        }
        .frame(height: AgendaCalendarFold.weekRowHeight)
        .frame(height: slotHeight, alignment: .bottom)
        .clipped()
        .opacity(isActive ? 1 : 1 - foldProgress)
        .accessibilityHidden(!isActive && isCollapsed)
    }

    func monthDate(offset: Int) -> Date {
        calendar.date(byAdding: .month, value: offset, to: visibleMonth) ?? visibleMonth
    }

    var monthPagerHeight: CGFloat {
        let currentHeight = gridHeight(containing: visibleMonth)
        guard monthDragOffset != 0 else { return currentHeight }
        let direction = monthDragOffset < 0 ? 1 : -1
        let targetHeight = gridHeight(containing: monthDate(offset: direction))
        let pagingProgress = min(abs(monthDragOffset) / max(monthPageWidth, 1), 1)
        return currentHeight + (targetHeight - currentHeight) * pagingProgress
    }

    func gridHeight(containing referenceDate: Date) -> CGFloat {
        AgendaCalendarFold.gridHeight(
            weekRowCount: AgendaCalendarMath.monthWeekRowCount(containing: referenceDate),
            progress: foldProgress
        )
    }

    func monthPagingGesture(pageWidth: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    return
                }
                monthDragOffset = value.translation.width
            }
            .onEnded { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    animateMonthDrag(to: 0)
                    handleVerticalDrag(value.translation)
                    return
                }

                let predictedDistance = value.predictedEndTranslation.width
                let shouldChangeMonth = abs(value.translation.width) > pageWidth * 0.2
                    || abs(predictedDistance) > pageWidth * 0.45
                guard shouldChangeMonth else {
                    animateMonthDrag(to: 0)
                    return
                }

                let direction = value.translation.width < 0 ? 1 : -1
                let targetOffset = direction > 0 ? -pageWidth : pageWidth
                completeMonthDrag(to: targetOffset, direction: direction)
            }
    }

    func animateMonthDrag(to offset: CGFloat) {
        if reduceMotion {
            monthDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                monthDragOffset = offset
            }
        }
    }

    func completeMonthDrag(to offset: CGFloat, direction: Int) {
        if reduceMotion {
            monthDragOffset = 0
            onChangeMonth(direction)
        } else {
            withAnimation(.snappy(duration: 0.22), completionCriteria: .logicallyComplete) {
                monthDragOffset = offset
            } completion: {
                onChangeMonth(direction)
            }
        }
    }
}
