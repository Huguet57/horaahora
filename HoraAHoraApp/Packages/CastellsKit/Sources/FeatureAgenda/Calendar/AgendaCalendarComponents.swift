import Foundation
import SwiftUI

extension AgendaCalendarView {
    var weekdayHeaderRow: some View {
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

    func dayButton(_ date: Date) -> some View {
        let hasEvents = eventDateKeys.contains(AgendaCalendarMath.localDateKey(date))
        return AgendaCalendarDayButton(
            date: date,
            selectedDate: selectedDate,
            hasEvents: hasEvents,
            onSelect: onSelect
        )
        .equatable()
    }

    var calendar: Calendar {
        AgendaCalendarMath.calendar
    }

    private var monthStart: Date {
        monthStart(containing: isCollapsed ? visibleWeek : visibleMonth)
    }

    func monthStart(containing date: Date) -> Date {
        calendar.dateInterval(of: .month, for: date)!.start
    }

    var monthTitle: String {
        AgendaCalendarMath.monthTitle(for: monthStart)
    }
}

struct AgendaCalendarDayButton: View, Equatable {
    let date: Date
    let selectedDate: Date
    let hasEvents: Bool
    let onSelect: (Date) -> Void

    nonisolated static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.date == rhs.date
            && lhs.selectedDate == rhs.selectedDate
            && lhs.hasEvents == rhs.hasEvents
    }

    var body: some View {
        let calendar = AgendaCalendarMath.calendar
        let selected = calendar.isDate(date, inSameDayAs: selectedDate)
        let today = calendar.isDateInToday(date)
        let isPast = calendar.compare(date, to: Date(), toGranularity: .day) == .orderedAscending

        Button { onSelect(date) } label: {
            ZStack {
                Circle()
                    .fill(selected ? Color.accentColor : .clear)
                    .frame(width: 42, height: 42)
                VStack(spacing: 1) {
                    Text(String(calendar.component(.day, from: date)))
                        .font(.body.monospacedDigit())
                        .foregroundStyle(
                            selected ? Color.white : today ? Color.accentColor : Color.primary
                        )
                    Circle()
                        .fill(hasEvents ? (selected ? Color.white : Color.accentColor) : .clear)
                        .frame(width: 5, height: 5)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44)
        }
        .buttonStyle(.plain)
        .opacity(isPast && !selected ? 0.35 : 1)
        .accessibilityLabel(AgendaCalendarMath.accessibilityDate(for: date))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityHint(hasEvents ? "Té actuacions" : "")
    }
}
