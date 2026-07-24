import Foundation
import SwiftUI

struct AgendaCalendarView: View {
    let selectedDate: Date
    let visibleMonth: Date
    let visibleWeek: Date
    let eventDateKeys: Set<String>
    /// Normalized fold progress `0...1`: 0 shows the whole month, 1 keeps only
    /// the visible week in the compact position.
    let foldProgress: CGFloat
    let onToggle: () -> Void
    let onSelect: (Date) -> Void
    let onChangeWeek: (Int) -> Void
    let onChangeMonth: (Int) -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var weekDragOffset: CGFloat = 0
    @State private var monthDragOffset: CGFloat = 0
    @State private var monthPageWidth: CGFloat = 1

    private let weekdays = ["DL", "DT", "DC", "DJ", "DV", "DS", "DG"]

    private var isCollapsed: Bool {
        AgendaCalendarFold.snapsCollapsed(progress: foldProgress)
    }

    private var isFullyFolded: Bool {
        foldProgress >= 0.999
    }

    var body: some View {
        VStack(spacing: 14) {
            header

            if isFullyFolded {
                weekPager
            } else {
                monthPager
            }
        }
        .contentShape(Rectangle())
        .accessibilityAction(named: "Setmana anterior") { onChangeWeek(-1) }
        .accessibilityAction(named: "Setmana següent") { onChangeWeek(1) }
        .onChange(of: visibleWeek) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                weekDragOffset = 0
            }
        }
        .onChange(of: visibleMonth) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                monthDragOffset = 0
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            Button(action: onToggle) {
                HStack(spacing: 7) {
                    Text(monthTitle)
                        .font(.title3.weight(.semibold))
                    Image(systemName: isCollapsed ? "chevron.down" : "chevron.up")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(
                isCollapsed ? "Mostra el calendari mensual" : "Plega el calendari mensual"
            )
            .accessibilityValue(isCollapsed ? "Plegat" : "Desplegat")
            Spacer()
            Button { changeVisiblePeriod(by: -1) } label: {
                Image(systemName: "chevron.left")
                    .font(.title2.weight(.semibold))
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel(isCollapsed ? "Setmana anterior" : "Mes anterior")
            Button { changeVisiblePeriod(by: 1) } label: {
                Image(systemName: "chevron.right")
                    .font(.title2.weight(.semibold))
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel(isCollapsed ? "Setmana següent" : "Mes següent")
        }
        .contentShape(Rectangle())
        .highPriorityGesture(calendarVerticalDragGesture)
    }

    private func changeVisiblePeriod(by offset: Int) {
        if isCollapsed {
            onChangeWeek(offset)
        } else {
            onChangeMonth(offset)
        }
    }

    private var calendarVerticalDragGesture: some Gesture {
        DragGesture(minimumDistance: 24)
            .onEnded { value in
                handleVerticalDrag(value.translation)
            }
    }

    private func handleVerticalDrag(_ translation: CGSize) {
        guard
            abs(translation.height) > abs(translation.width),
            abs(translation.height) >= 36
        else {
            return
        }

        if translation.height < 0, !isCollapsed {
            onToggle()
        } else if translation.height > 0, isCollapsed {
            onToggle()
        }
    }

    // MARK: - Month pager

    private var monthPager: some View {
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

    private func monthGrid(containing referenceDate: Date) -> some View {
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
    private func monthWeekRow(_ dates: [Date], in month: Date, isActive: Bool) -> some View {
        let slotHeight = isActive
            ? AgendaCalendarFold.weekRowSlotHeight
            : AgendaCalendarFold.inactiveWeekRowSlotHeight(progress: foldProgress)

        return HStack(spacing: 4) {
            ForEach(dates, id: \.self) { date in
                if calendar.isDate(date, equalTo: month, toGranularity: .month) {
                    dayButton(date)
                } else if isActive {
                    // Adjacent-month day completing the active week across a
                    // month boundary. It fades in as the fold progresses.
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

    private func monthDate(offset: Int) -> Date {
        calendar.date(byAdding: .month, value: offset, to: visibleMonth) ?? visibleMonth
    }

    private var monthPagerHeight: CGFloat {
        let currentHeight = gridHeight(containing: visibleMonth)
        guard monthDragOffset != 0 else { return currentHeight }
        let direction = monthDragOffset < 0 ? 1 : -1
        let targetHeight = gridHeight(containing: monthDate(offset: direction))
        let pagingProgress = min(abs(monthDragOffset) / max(monthPageWidth, 1), 1)
        return currentHeight + (targetHeight - currentHeight) * pagingProgress
    }

    private func gridHeight(containing referenceDate: Date) -> CGFloat {
        AgendaCalendarFold.gridHeight(
            weekRowCount: AgendaCalendarMath.monthWeekRows(containing: referenceDate).count,
            progress: foldProgress
        )
    }

    private func monthPagingGesture(pageWidth: CGFloat) -> some Gesture {
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

    private func animateMonthDrag(to offset: CGFloat) {
        if reduceMotion {
            monthDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                monthDragOffset = offset
            }
        }
    }

    private func completeMonthDrag(to offset: CGFloat, direction: Int) {
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

    // MARK: - Week pager

    private var weekPager: some View {
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

    private func weekGrid(containing referenceDate: Date) -> some View {
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

    private func weekDate(offset: Int) -> Date {
        calendar.date(byAdding: .day, value: offset * 7, to: visibleWeek) ?? visibleWeek
    }

    private func weekPagingGesture(pageWidth: CGFloat) -> some Gesture {
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

    private func animateWeekDrag(to offset: CGFloat) {
        if reduceMotion {
            weekDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                weekDragOffset = offset
            }
        }
    }

    private func completeWeekDrag(to offset: CGFloat, direction: Int) {
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

    // MARK: - Shared pieces

    private var weekdayHeaderRow: some View {
        HStack(spacing: 4) {
            ForEach(weekdays, id: \.self) { weekday in
                Text(weekday)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.tertiary)
                    .frame(maxWidth: .infinity)
            }
        }
        .frame(height: AgendaCalendarFold.weekdayHeaderHeight)
    }

    private func dayButton(_ date: Date) -> some View {
        let selected = calendar.isDate(date, inSameDayAs: selectedDate)
        let today = calendar.isDateInToday(date)
        let isPast = calendar.compare(date, to: Date(), toGranularity: .day) == .orderedAscending
        let hasEvents = eventDateKeys.contains(localDateKey(date))
        return Button { onSelect(date) } label: {
            ZStack {
                Circle()
                    .fill(selected ? Color.accentColor : .clear)
                    .frame(width: 42, height: 42)
                VStack(spacing: 1) {
                    Text(String(calendar.component(.day, from: date)))
                        .font(.body.monospacedDigit())
                        .foregroundStyle(selected ? Color.white : today ? Color.accentColor : Color.primary)
                    Circle()
                        .fill(hasEvents ? (selected ? Color.white : Color.accentColor) : .clear)
                        .frame(width: 5, height: 5)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44)
        }
        .buttonStyle(.plain)
        .opacity(isPast && !selected ? 0.35 : 1)
        .accessibilityLabel(accessibilityDate(date))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityHint(hasEvents ? "Té actuacions" : "")
    }

    private var calendar: Calendar {
        AgendaCalendarMath.calendar
    }

    private var monthStart: Date {
        monthStart(containing: isCollapsed ? visibleWeek : visibleMonth)
    }

    private func monthStart(containing date: Date) -> Date {
        calendar.dateInterval(of: .month, for: date)!.start
    }

    private var monthTitle: String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "LLLL 'del' yyyy"
        return formatter.string(from: monthStart)
    }

    private func localDateKey(_ date: Date) -> String {
        AgendaCalendarMath.localDateKey(date)
    }

    private func accessibilityDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateStyle = .full
        return formatter.string(from: date)
    }
}
