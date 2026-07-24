import Foundation

/// Date math for the agenda: Monday-based weeks in the `Europe/Madrid`
/// timezone, month grids and prefetch windows.
enum AgendaCalendarMath {
    static var calendar: Calendar {
        var value = Calendar(identifier: .gregorian)
        value.locale = Locale(identifier: "ca_ES")
        value.timeZone = TimeZone(identifier: "Europe/Madrid")!
        value.firstWeekday = 2
        return value
    }

    static func week(containing date: Date) -> [Date] {
        let startOfDay = calendar.startOfDay(for: date)
        let weekday = calendar.component(.weekday, from: startOfDay)
        let daysSinceMonday = (weekday - calendar.firstWeekday + 7) % 7
        guard let monday = calendar.date(byAdding: .day, value: -daysSinceMonday, to: startOfDay) else {
            return []
        }
        return (0..<7).compactMap { calendar.date(byAdding: .day, value: $0, to: monday) }
    }

    /// Full weeks (Monday-based) covering the month that contains `date`.
    /// Every row has 7 days, including adjacent-month days at both ends.
    static func monthWeekRows(containing date: Date) -> [[Date]] {
        guard
            let interval = calendar.dateInterval(of: .month, for: date),
            let lastDay = calendar.date(byAdding: .day, value: -1, to: interval.end),
            var rowStart = week(containing: interval.start).first
        else { return [] }

        var rows: [[Date]] = []
        while rowStart <= lastDay {
            rows.append((0..<7).compactMap {
                calendar.date(byAdding: .day, value: $0, to: rowStart)
            })
            guard let next = calendar.date(byAdding: .day, value: 7, to: rowStart) else { break }
            rowStart = next
        }
        return rows
    }

    /// Index of the row containing `date`, counting adjacent-month days that
    /// complete the first and last weeks. `nil` when the day is outside the grid.
    static func weekRowIndex(of date: Date, in rows: [[Date]]) -> Int? {
        rows.firstIndex { row in
            row.contains { calendar.isDate($0, inSameDayAs: date) }
        }
    }

    static func prefetchRanges(containing date: Date) -> [(start: Date, end: Date)] {
        guard
            let monthInterval = calendar.dateInterval(of: .month, for: date),
            let windowStart = calendar.date(byAdding: .month, value: -6, to: monthInterval.start),
            let currentMonthEnd = calendar.date(byAdding: .day, value: -1, to: monthInterval.end),
            let windowEndExclusive = calendar.date(byAdding: .month, value: 6, to: monthInterval.end),
            let windowEnd = calendar.date(byAdding: .day, value: -1, to: windowEndExclusive)
        else { return [] }

        return [
            (windowStart, currentMonthEnd),
            (monthInterval.end, windowEnd)
        ]
    }

    static func monthRange(containing date: Date) -> (start: Date, end: Date)? {
        guard
            let interval = calendar.dateInterval(of: .month, for: date),
            let end = calendar.date(byAdding: .day, value: -1, to: interval.end)
        else { return nil }

        return (interval.start, end)
    }

    static func localDateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    static func monthKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM"
        return formatter.string(from: date)
    }

    static func monthStarts(from start: Date, through end: Date) -> [Date] {
        guard var month = calendar.dateInterval(of: .month, for: start)?.start else { return [] }
        var result: [Date] = []
        while month <= end {
            result.append(month)
            guard let next = calendar.date(byAdding: .month, value: 1, to: month) else { break }
            month = next
        }
        return result
    }
}
