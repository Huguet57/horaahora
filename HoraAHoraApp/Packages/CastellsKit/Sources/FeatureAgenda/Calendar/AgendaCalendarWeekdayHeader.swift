import SwiftUI

extension AgendaCalendarView {
    var weekdayHeaderRow: some View {
        AgendaCalendarWeekdayHeader(weekdays: weekdays)
    }
}

struct AgendaCalendarWeekdayHeader: View {
    let weekdays: [String]

    var body: some View {
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
}
