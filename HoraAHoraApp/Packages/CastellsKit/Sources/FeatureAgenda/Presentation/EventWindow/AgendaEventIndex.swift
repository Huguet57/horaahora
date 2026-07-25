import Foundation
import CastellsDomain

struct AgendaEventIndex {
    private struct Entry {
        let event: CastellEvent
        let participatingGroupKeys: Set<String>
    }

    private let entriesByDate: [String: [Entry]]
    private let entriesByMonth: [String: [Entry]]
    private let participatingGroupKeysByDate: [String: Set<String>]

    init(events: [CastellEvent]) {
        let entries = events.map { event in
            Entry(
                event: event,
                participatingGroupKeys: Set(
                    event.participatingGroups.map(AgendaGroupNameNormalizer.key)
                )
            )
        }
        let entriesByDate = Dictionary(grouping: entries) { $0.event.localDate }
        self.entriesByDate = entriesByDate
        self.entriesByMonth = Dictionary(grouping: entries) {
            String($0.event.localDate.prefix(7))
        }
        self.participatingGroupKeysByDate = entriesByDate.mapValues { entries in
            entries.reduce(into: Set<String>()) { keys, entry in
                keys.formUnion(entry.participatingGroupKeys)
            }
        }
    }

    var dateKeys: Set<String> {
        Set(entriesByDate.keys)
    }

    func events(on date: Date) -> [CastellEvent] {
        let dateKey = AgendaCalendarMath.localDateKey(date)
        return entriesByDate[dateKey, default: []].map(\.event)
    }

    func events(inMonthContaining date: Date) -> [CastellEvent] {
        entriesByMonth[AgendaCalendarMath.monthKey(date), default: []].map(\.event)
    }

    func projection(
        on selectedDate: Date,
        inMonthContaining visibleMonth: Date,
        matchingGroupKeys matches: (Set<String>) -> Bool
    ) -> AgendaEventWindowProjection {
        let selectedDateKey = AgendaCalendarMath.localDateKey(selectedDate)
        var matchingDayEvents: [CastellEvent] = []
        var otherDayEvents: [CastellEvent] = []
        for entry in entriesByDate[selectedDateKey, default: []] {
            if matches(entry.participatingGroupKeys) {
                matchingDayEvents.append(entry.event)
            } else {
                otherDayEvents.append(entry.event)
            }
        }

        let matchingDateKeys = Set(
            participatingGroupKeysByDate.compactMap { dateKey, groupKeys in
                matches(groupKeys) ? dateKey : nil
            }
        )
        let visibleMonthKey = AgendaCalendarMath.monthKey(visibleMonth)
        let matchingMonthEvents = entriesByMonth[visibleMonthKey, default: []].compactMap { entry in
            matches(entry.participatingGroupKeys) ? entry.event : nil
        }

        return AgendaEventWindowProjection(
            events: matchingDayEvents,
            otherEvents: otherDayEvents,
            eventDateKeys: matchingDateKeys,
            monthEvents: matchingMonthEvents
        )
    }
}
