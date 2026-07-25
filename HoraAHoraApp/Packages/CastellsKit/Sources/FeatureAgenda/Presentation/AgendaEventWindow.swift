import Foundation
import CastellsDomain

struct AgendaEventWindow {
    private var allEvents: [CastellEvent] = []
    private var eventsByDate: [String: [CastellEvent]] = [:]
    private var eventsByMonth: [String: [CastellEvent]] = [:]
    private var participatingGroupKeysByEventKey: [String: Set<String>] = [:]
    private var participatingGroupKeysByDate: [String: Set<String>] = [:]
    private var loadedMonthKeys: Set<String> = []

    var isEmpty: Bool {
        allEvents.isEmpty
    }

    var dateKeys: Set<String> {
        Set(eventsByDate.keys)
    }

    var participatingGroupNames: [String] {
        allEvents.flatMap(\.participatingGroups)
    }

    func containsMonth(_ date: Date) -> Bool {
        loadedMonthKeys.contains(AgendaCalendarMath.monthKey(date))
    }

    func events(on date: Date) -> [CastellEvent] {
        let dateKey = AgendaCalendarMath.localDateKey(date)
        return eventsByDate[dateKey, default: []]
    }

    func events(inMonthContaining date: Date) -> [CastellEvent] {
        eventsByMonth[AgendaCalendarMath.monthKey(date), default: []]
    }

    func projection(
        on selectedDate: Date,
        inMonthContaining visibleMonth: Date,
        matchingGroupKeys matches: (Set<String>) -> Bool
    ) -> AgendaEventWindowProjection {
        var matchingDayEvents: [CastellEvent] = []
        var otherDayEvents: [CastellEvent] = []
        for event in events(on: selectedDate) {
            if matches(participatingGroupKeys(for: event)) {
                matchingDayEvents.append(event)
            } else {
                otherDayEvents.append(event)
            }
        }

        let matchingDateKeys = Set(
            participatingGroupKeysByDate.compactMap { dateKey, groupKeys in
                matches(groupKeys) ? dateKey : nil
            }
        )
        let matchingMonthEvents = events(inMonthContaining: visibleMonth).filter {
            matches(participatingGroupKeys(for: $0))
        }

        return AgendaEventWindowProjection(
            events: matchingDayEvents,
            otherEvents: otherDayEvents,
            eventDateKeys: matchingDateKeys,
            monthEvents: matchingMonthEvents
        )
    }

    mutating func replace(from start: Date, through end: Date, with events: [CastellEvent]) {
        let lower = AgendaCalendarMath.localDateKey(start)
        let upper = AgendaCalendarMath.localDateKey(end)
        allEvents.removeAll { lower <= $0.localDate && $0.localDate <= upper }
        allEvents.append(contentsOf: events)
        allEvents = Self.uniqueAndSorted(allEvents)
        rebuildIndexes()
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

    private mutating func rebuildIndexes() {
        eventsByDate = Dictionary(grouping: allEvents, by: \.localDate)
        eventsByMonth = Dictionary(grouping: allEvents) {
            String($0.localDate.prefix(7))
        }
        participatingGroupKeysByEventKey.removeAll(keepingCapacity: true)
        participatingGroupKeysByDate.removeAll(keepingCapacity: true)

        for event in allEvents {
            let groupKeys = Set(event.participatingGroups.map(AgendaGroupNameNormalizer.key))
            participatingGroupKeysByEventKey[Self.eventKey(event)] = groupKeys
            participatingGroupKeysByDate[event.localDate, default: []].formUnion(groupKeys)
        }
    }

    private func participatingGroupKeys(for event: CastellEvent) -> Set<String> {
        participatingGroupKeysByEventKey[Self.eventKey(event), default: []]
    }

    private static func eventKey(_ event: CastellEvent) -> String {
        "\(event.sourceID):\(event.externalID)"
    }
}

struct AgendaEventWindowProjection {
    let events: [CastellEvent]
    let otherEvents: [CastellEvent]
    let eventDateKeys: Set<String>
    let monthEvents: [CastellEvent]
}
