import Foundation
import CastellsDomain

struct AgendaEventWindow {
    private var allEvents: [CastellEvent] = []
    private var index = AgendaEventIndex(events: [])
    private var loadedMonthKeys: Set<String> = []

    var isEmpty: Bool {
        allEvents.isEmpty
    }

    var dateKeys: Set<String> {
        index.dateKeys
    }

    var participatingGroupNames: [String] {
        allEvents.flatMap(\.participatingGroups)
    }

    func containsMonth(_ date: Date) -> Bool {
        loadedMonthKeys.contains(AgendaCalendarMath.monthKey(date))
    }

    func events(on date: Date) -> [CastellEvent] {
        index.events(on: date)
    }

    func events(inMonthContaining date: Date) -> [CastellEvent] {
        index.events(inMonthContaining: date)
    }

    func projection(
        on selectedDate: Date,
        inMonthContaining visibleMonth: Date,
        matchingGroupKeys matches: (Set<String>) -> Bool
    ) -> AgendaEventWindowProjection {
        index.projection(
            on: selectedDate,
            inMonthContaining: visibleMonth,
            matchingGroupKeys: matches
        )
    }

    mutating func replace(from start: Date, through end: Date, with events: [CastellEvent]) {
        let lower = AgendaCalendarMath.localDateKey(start)
        let upper = AgendaCalendarMath.localDateKey(end)
        allEvents.removeAll { lower <= $0.localDate && $0.localDate <= upper }
        allEvents.append(contentsOf: events)
        allEvents = Self.uniqueAndSorted(allEvents)
        index = AgendaEventIndex(events: allEvents)
    }

    mutating func markLoaded(from start: Date, through end: Date) {
        loadedMonthKeys.formUnion(
            AgendaCalendarMath.monthStarts(from: start, through: end)
                .map(AgendaCalendarMath.monthKey)
        )
    }

    mutating func markLoaded(monthStartingAt date: Date) {
        loadedMonthKeys.insert(AgendaCalendarMath.monthKey(date))
    }

    private static func uniqueAndSorted(_ events: [CastellEvent]) -> [CastellEvent] {
        var seen = Set<String>()
        return events
            .filter { seen.insert("\($0.sourceID):\($0.externalID)").inserted }
            .sorted {
                if $0.localDate == $1.localDate { return $0.sourceOrder < $1.sourceOrder }
                return $0.localDate < $1.localDate
            }
    }
}
