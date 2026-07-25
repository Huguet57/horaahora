import Foundation
import CastellsDomain

enum HourByHourDayGrouping {
    static func groups(
        from items: [HourByHourItem],
        calendar: Calendar = .autoupdatingCurrent
    ) -> [HourByHourDayGroup] {
        var orderedDays: [Date?] = []
        var itemsByDay: [Date?: [HourByHourItem]] = [:]

        for item in items {
            let day = item.publishedAt.map { calendar.startOfDay(for: $0) }
            if itemsByDay[day] == nil {
                orderedDays.append(day)
            }
            itemsByDay[day, default: []].append(item)
        }

        return orderedDays.map { day in
            HourByHourDayGroup(
                id: identifier(for: day),
                day: day,
                items: itemsByDay[day] ?? []
            )
        }
    }

    private static func identifier(for day: Date?) -> String {
        guard let day else { return "undated" }
        return "day-\(day.timeIntervalSinceReferenceDate.bitPattern)"
    }
}

public struct HourByHourDayGroup: Identifiable {
    public let id: String
    public let day: Date?
    public let items: [HourByHourItem]
}
