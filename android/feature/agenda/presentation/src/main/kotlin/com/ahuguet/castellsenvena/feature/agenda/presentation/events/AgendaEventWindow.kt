package com.ahuguet.castellsenvena.feature.agenda.presentation.events

import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupNameNormalizer
import java.time.LocalDate

/** What the Agenda shows for the selected day and the visible month. */
internal data class AgendaEventWindowProjection(
    /** The selected day's events that match the group filter. */
    val events: List<CastellEvent>,
    /** The selected day's events of groups the user does not follow. */
    val otherEvents: List<CastellEvent>,
    /** Days with matching events, to mark them in the calendar. */
    val eventDateKeys: Set<String>,
    /** The visible month's matching events. */
    val monthEvents: List<CastellEvent>,
)

/** Lookups by day and by month, with the normalized group keys precomputed. */
internal class AgendaEventIndex(events: List<CastellEvent>) {
    private class Entry(val event: CastellEvent, val participatingGroupKeys: Set<String>)

    private val entriesByDate: Map<String, List<Entry>>
    private val entriesByMonth: Map<String, List<Entry>>
    private val participatingGroupKeysByDate: Map<String, Set<String>>

    init {
        val entries = events.map { event ->
            Entry(event, event.participatingGroups.mapTo(HashSet(), AgendaGroupNameNormalizer::key))
        }
        entriesByDate = entries.groupBy { it.event.localDate }
        entriesByMonth = entries.groupBy { it.event.localDate.take(7) }
        participatingGroupKeysByDate = entriesByDate.mapValues { (_, dayEntries) ->
            dayEntries.flatMapTo(HashSet()) { it.participatingGroupKeys }
        }
    }

    val dateKeys: Set<String> get() = entriesByDate.keys

    fun eventsOn(date: LocalDate): List<CastellEvent> =
        entriesByDate[AgendaCalendarMath.localDateKey(date)].orEmpty().map { it.event }

    fun eventsInMonth(containing: LocalDate): List<CastellEvent> =
        entriesByMonth[AgendaCalendarMath.monthKey(containing)].orEmpty().map { it.event }

    fun projection(
        selectedDate: LocalDate,
        visibleMonth: LocalDate,
        matches: (Set<String>) -> Boolean,
    ): AgendaEventWindowProjection {
        val (dayEvents, otherDayEvents) = entriesByDate[AgendaCalendarMath.localDateKey(selectedDate)]
            .orEmpty()
            .partition { matches(it.participatingGroupKeys) }
        return AgendaEventWindowProjection(
            events = dayEvents.map { it.event },
            otherEvents = otherDayEvents.map { it.event },
            eventDateKeys = participatingGroupKeysByDate.filterValues(matches).keys,
            monthEvents = entriesByMonth[AgendaCalendarMath.monthKey(visibleMonth)]
                .orEmpty()
                .filter { matches(it.participatingGroupKeys) }
                .map { it.event },
        )
    }
}

/**
 * The events prefetched around the visible month, deduplicated and sorted,
 * and which months have already been loaded.
 */
internal class AgendaEventWindow {
    private var allEvents: List<CastellEvent> = emptyList()
    private var index = AgendaEventIndex(emptyList())
    private val loadedMonthKeys = mutableSetOf<String>()

    val isEmpty: Boolean get() = allEvents.isEmpty()

    val dateKeys: Set<String> get() = index.dateKeys

    val participatingGroupNames: List<String> get() = allEvents.flatMap { it.participatingGroups }

    fun containsMonth(date: LocalDate): Boolean = AgendaCalendarMath.monthKey(date) in loadedMonthKeys

    fun eventsOn(date: LocalDate): List<CastellEvent> = index.eventsOn(date)

    fun eventsInMonth(containing: LocalDate): List<CastellEvent> = index.eventsInMonth(containing)

    fun projection(
        selectedDate: LocalDate,
        visibleMonth: LocalDate,
        matches: (Set<String>) -> Boolean,
    ): AgendaEventWindowProjection = index.projection(selectedDate, visibleMonth, matches)

    /** Replaces every event between [from] and [through] with [events]. */
    fun replace(from: LocalDate, through: LocalDate, events: List<CastellEvent>) {
        val range = AgendaCalendarMath.localDateKey(from)..AgendaCalendarMath.localDateKey(through)
        allEvents = (allEvents.filterNot { it.localDate in range } + events)
            .distinctBy { it.sourceId to it.externalId }
            .sortedWith(compareBy<CastellEvent> { it.localDate }.thenBy { it.sourceOrder })
        index = AgendaEventIndex(allEvents)
    }

    fun markLoaded(from: LocalDate, through: LocalDate) {
        AgendaCalendarMath.monthStarts(from, through).mapTo(loadedMonthKeys, AgendaCalendarMath::monthKey)
    }

    fun markLoaded(monthStartingAt: LocalDate) {
        loadedMonthKeys += AgendaCalendarMath.monthKey(monthStartingAt)
    }
}
