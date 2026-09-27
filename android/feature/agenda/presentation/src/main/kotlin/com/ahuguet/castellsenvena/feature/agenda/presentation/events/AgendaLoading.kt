package com.ahuguet.castellsenvena.feature.agenda.presentation.events

import com.ahuguet.castellsenvena.core.common.runCatchingCancellable
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.DateRange
import java.time.LocalDate

internal data class AgendaFetchResult(
    val items: List<CastellEvent>,
    val fromCache: Boolean,
    val sourceStatus: AgendaSourceStatus,
)

/** Loads every page of a date range. Only the first request forces the source. */
internal class AgendaPageLoader(private val repository: AgendaRepository) {
    suspend fun fetch(range: DateRange, forceRefresh: Boolean): AgendaFetchResult {
        var cursor: String? = null
        val collected = mutableListOf<CastellEvent>()
        var allFromCache = true
        var allActive = true
        do {
            val page = repository.events(
                from = range.start,
                to = range.end,
                group = null,
                municipality = null,
                cursor = cursor,
                limit = PAGE_SIZE,
                forceRefresh = forceRefresh && cursor == null,
            )
            collected += page.items
            allFromCache = allFromCache && page.fromCache
            allActive = allActive && page.sourceStatus == AgendaSourceStatus.ACTIVE
            cursor = page.nextCursor
        } while (cursor != null)

        return AgendaFetchResult(
            items = collected,
            fromCache = allFromCache,
            sourceStatus = if (allActive) AgendaSourceStatus.ACTIVE else AgendaSourceStatus.UNAVAILABLE,
        )
    }

    private companion object {
        const val PAGE_SIZE = 100
    }
}

/**
 * Reads the stored events of a prefetch window once. Asking again for the same
 * window reports whether it had a snapshot without reading the database.
 */
internal class AgendaCacheWindowReader(private val repository: AgendaRepository) {
    data class Window(val start: LocalDate, val end: LocalDate, val items: List<CastellEvent>)

    data class Lookup(val hasSnapshot: Boolean, val windowToApply: Window?)

    private data class State(val startKey: String, val endKey: String, val hasSnapshot: Boolean)

    private var state: State? = null

    suspend fun lookup(ranges: List<DateRange>): Lookup {
        val first = ranges.firstOrNull() ?: return Lookup(hasSnapshot = false, windowToApply = null)
        val last = ranges.last()
        val startKey = AgendaCalendarMath.localDateKey(first.start)
        val endKey = AgendaCalendarMath.localDateKey(last.end)
        state?.let { previous ->
            if (previous.startKey == startKey && previous.endKey == endKey) {
                return Lookup(hasSnapshot = previous.hasSnapshot, windowToApply = null)
            }
        }

        val cached = ranges.flatMap { range ->
            runCatchingCancellable {
                repository.cachedEvents(from = range.start, to = range.end, group = null, municipality = null)
            }.getOrDefault(emptyList())
        }
        val hasSnapshot = cached.isNotEmpty()
        state = State(startKey, endKey, hasSnapshot)
        return Lookup(
            hasSnapshot = hasSnapshot,
            windowToApply = if (hasSnapshot) Window(first.start, last.end, cached) else null,
        )
    }

    fun reset() {
        state = null
    }
}
