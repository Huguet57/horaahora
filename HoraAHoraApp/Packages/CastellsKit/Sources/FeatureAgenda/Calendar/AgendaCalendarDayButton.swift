import Foundation
import SwiftUI

extension AgendaCalendarView {
    func dayButton(_ date: Date) -> some View {
        AgendaCalendarDayButton(
            date: date,
            selectedDate: selectedDate,
            hasEvents: eventDateKeys.contains(AgendaCalendarMath.localDateKey(date)),
            onSelect: onSelect
        )
        .equatable()
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
