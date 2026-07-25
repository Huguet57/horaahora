import Foundation

extension AgendaCalendarView {
    var calendar: Calendar {
        AgendaCalendarMath.calendar
    }

    func monthStart(containing date: Date) -> Date {
        calendar.dateInterval(of: .month, for: date)!.start
    }

    var monthTitle: String {
        let referenceDate = isCollapsed ? visibleWeek : visibleMonth
        return AgendaCalendarMath.monthTitle(for: monthStart(containing: referenceDate))
    }
}
