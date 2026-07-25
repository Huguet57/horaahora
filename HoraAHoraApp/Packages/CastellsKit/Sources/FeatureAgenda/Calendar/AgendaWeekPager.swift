import Foundation
import SwiftUI

extension AgendaCalendarView {
    var weekPager: some View {
        GeometryReader { geometry in
            let pageWidth = geometry.size.width
            HStack(spacing: 0) {
                weekGrid(containing: weekDate(offset: -1))
                    .frame(width: pageWidth)
                weekGrid(containing: visibleWeek)
                    .frame(width: pageWidth)
                weekGrid(containing: weekDate(offset: 1))
                    .frame(width: pageWidth)
            }
            .frame(width: pageWidth * 3, alignment: .leading)
            .offset(x: -pageWidth + weekDragOffset)
            .contentShape(Rectangle())
            .highPriorityGesture(weekPagingGesture(pageWidth: pageWidth))
        }
        .frame(height: AgendaCalendarFold.collapsedGridHeight)
        .clipped()
    }

    func weekGrid(containing referenceDate: Date) -> some View {
        VStack(spacing: 0) {
            weekdayHeaderRow

            HStack(spacing: 4) {
                ForEach(AgendaCalendarMath.week(containing: referenceDate), id: \.self) { date in
                    dayButton(date)
                }
            }
            .frame(height: AgendaCalendarFold.weekRowHeight)
            .frame(height: AgendaCalendarFold.weekRowSlotHeight, alignment: .bottom)
        }
    }

    func weekDate(offset: Int) -> Date {
        calendar.date(byAdding: .day, value: offset * 7, to: visibleWeek) ?? visibleWeek
    }

    func weekPagingGesture(pageWidth: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    return
                }
                weekDragOffset = value.translation.width
            }
            .onEnded { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    animateWeekDrag(to: 0)
                    handleVerticalDrag(value.translation)
                    return
                }

                let predictedDistance = value.predictedEndTranslation.width
                let shouldChangeWeek = abs(value.translation.width) > pageWidth * 0.2
                    || abs(predictedDistance) > pageWidth * 0.45
                guard shouldChangeWeek else {
                    animateWeekDrag(to: 0)
                    return
                }

                let direction = value.translation.width < 0 ? 1 : -1
                let targetOffset = direction > 0 ? -pageWidth : pageWidth
                completeWeekDrag(to: targetOffset, direction: direction)
            }
    }

    func animateWeekDrag(to offset: CGFloat) {
        if reduceMotion {
            weekDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                weekDragOffset = offset
            }
        }
    }

    func completeWeekDrag(to offset: CGFloat, direction: Int) {
        if reduceMotion {
            weekDragOffset = 0
            onChangeWeek(direction)
        } else {
            withAnimation(.snappy(duration: 0.22), completionCriteria: .logicallyComplete) {
                weekDragOffset = offset
            } completion: {
                onChangeWeek(direction)
            }
        }
    }
}
