package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.core.common.runCatchingCancellable
import com.ahuguet.castellsenvena.core.common.userMessage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.core.domain.groups.GroupDirectoryRepository
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarPaging
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.DateRange
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaCacheWindowReader
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaEventWindow
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaFetchResult
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaPageLoader
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupFilter
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupFilterState
import java.time.LocalDate
import java.time.YearMonth
import java.time.temporal.ChronoUnit
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AgendaState(
    val selectedDate: LocalDate,
    val visibleMonth: LocalDate,
    val visibleWeek: LocalDate,
    val monthEvents: List<CastellEvent> = emptyList(),
    val events: List<CastellEvent> = emptyList(),
    val otherEvents: List<CastellEvent> = emptyList(),
    val eventDateKeys: Set<String> = emptySet(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isFromCache: Boolean = false,
    val sourceStatus: AgendaSourceStatus = AgendaSourceStatus.UNAVAILABLE,
    val groupDirectoryErrorMessage: String? = null,
    val groupFilter: AgendaGroupFilterState = AgendaGroupFilterState(),
)

/**
 * The Agenda: a calendar whose month and week can be browsed without waiting,
 * because six months around the visible one are prefetched and stored.
 */
class AgendaViewModel(
    repository: AgendaRepository,
    private val groupDirectoryRepository: GroupDirectoryRepository? = null,
    filterStore: AgendaFilterStore? = null,
    today: LocalDate = AgendaCalendarMath.today(),
) {
    val officialUrl: String = repository.officialUrl

    private val pageLoader = AgendaPageLoader(repository)
    private val cacheReader = AgendaCacheWindowReader(repository)
    private val eventWindow = AgendaEventWindow()
    private val groupFilter = AgendaGroupFilter(filterStore)
    private val monthsBeingPrefetched = mutableSetOf<String>()
    private var hasStartedInitialLoad = false
    private var isLoadInFlight = false

    private val mutableState = MutableStateFlow(
        AgendaState(
            selectedDate = today,
            visibleMonth = today,
            visibleWeek = today,
            groupFilter = groupFilter.snapshot(),
        ),
    )
    val state: StateFlow<AgendaState> = mutableState.asStateFlow()

    private val current: AgendaState get() = mutableState.value

    /** The selected day. Setting it does not move the visible month or week. */
    var selectedDate: LocalDate
        get() = current.selectedDate
        set(value) {
            mutableState.value = current.copy(selectedDate = value)
        }

    val groupSelection: AgendaGroupSelection get() = groupFilter.selection

    /** Shows the stored events at once, before any network request. */
    suspend fun preloadFromCache() {
        if (!hasStartedInitialLoad) {
            mutableState.value = current.copy(visibleMonth = current.selectedDate, visibleWeek = current.selectedDate)
        }
        restoreCachedSnapshot(AgendaCalendarMath.prefetchRanges(current.visibleMonth))
    }

    fun select(date: LocalDate) {
        mutableState.value = current.copy(selectedDate = date, visibleMonth = date, visibleWeek = date)
        updateVisibleMonthEvents()
    }

    suspend fun selectAndLoad(date: LocalDate) {
        select(date)
        extendPrefetchWindowIfNeeded(containing = date)
    }

    suspend fun changeMonth(offset: Int) {
        val month = current.visibleMonth.plusMonths(offset.toLong())
        mutableState.value = current.copy(visibleMonth = month)
        updateVisibleMonthEvents()
        extendPrefetchWindowIfNeeded(containing = month)
    }

    suspend fun changeWeek(offset: Int) {
        val week = current.visibleWeek.plusWeeks(offset.toLong())
        mutableState.value = current.copy(visibleWeek = week)
        extendPrefetchWindowIfNeeded(containing = week)
    }

    /**
     * Shows the month that contains [date]. Pagers settle on absolute months,
     * so the offset is measured when the change runs, not when it is requested.
     */
    suspend fun showMonth(containing: LocalDate) {
        val offset = ChronoUnit.MONTHS.between(YearMonth.from(current.visibleMonth), YearMonth.from(containing))
        if (offset != 0L) changeMonth(offset.toInt())
    }

    /** Shows the week that contains [date], like [showMonth]. */
    suspend fun showWeek(containing: LocalDate) {
        val offset = ChronoUnit.WEEKS.between(
            AgendaCalendarPaging.monday(current.visibleWeek),
            AgendaCalendarPaging.monday(containing),
        )
        if (offset != 0L) changeWeek(offset.toInt())
    }

    /** Loads the prefetch window around the visible month; stored events show meanwhile. */
    suspend fun load(forceRefresh: Boolean = false) {
        if (isLoadInFlight) return
        isLoadInFlight = true
        try {
            mutableState.value = current.copy(errorMessage = null)
            if (!hasStartedInitialLoad) {
                mutableState.value = current.copy(visibleMonth = current.selectedDate, visibleWeek = current.selectedDate)
                hasStartedInitialLoad = true
            }
            val ranges = AgendaCalendarMath.prefetchRanges(current.visibleMonth)
            val hasCachedSnapshot = !forceRefresh && restoreCachedSnapshot(ranges)
            mutableState.value = current.copy(isLoading = !hasCachedSnapshot)
            try {
                val results = coroutineScope {
                    ranges.map { range -> async { pageLoader.fetch(range, forceRefresh) } }.awaitAll()
                }
                applyPrefetchedWindow(
                    from = ranges.first().start,
                    through = ranges.last().end,
                    items = results.flatMap(AgendaFetchResult::items),
                    sourceStatus = if (results.all { it.sourceStatus == AgendaSourceStatus.ACTIVE }) {
                        AgendaSourceStatus.ACTIVE
                    } else {
                        AgendaSourceStatus.UNAVAILABLE
                    },
                    fromCache = results.all(AgendaFetchResult::fromCache),
                )
                cacheReader.reset()
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (failure: Exception) {
                // A stored snapshot stays on screen; the next load retries silently.
                if (!hasCachedSnapshot) mutableState.value = current.copy(errorMessage = failure.userMessage())
            }
        } finally {
            mutableState.value = current.copy(isLoading = false)
            isLoadInFlight = false
        }
    }

    /** Retry after an error: reloads the visible month and keeps its events on screen meanwhile. */
    suspend fun refresh() {
        if (isLoadInFlight) return
        isLoadInFlight = true
        try {
            mutableState.value = current.copy(errorMessage = null)
            val range = AgendaCalendarMath.monthRange(current.visibleMonth)
            try {
                val result = pageLoader.fetch(range, forceRefresh = true)
                applyPrefetchedWindow(range.start, range.end, result.items, result.sourceStatus, result.fromCache)
                cacheReader.reset()
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (failure: Exception) {
                if (eventWindow.isEmpty) mutableState.value = current.copy(errorMessage = failure.userMessage())
            }
        } finally {
            isLoadInFlight = false
        }
    }

    // Group filter

    fun isFollowing(groupName: String): Boolean = groupFilter.isFollowing(groupName)

    fun isFeatured(groupName: String): Boolean = groupFilter.isFeatured(groupName)

    fun setFollowing(following: Boolean, groupName: String) = changeSelection {
        groupFilter.setFollowing(following, groupName)
    }

    fun followAllGroups() = changeSelection { groupFilter.followAll() }

    fun toggleFollowingAllGroups() = changeSelection { groupFilter.toggleFollowingAll() }

    fun toggleFollowingFeaturedGroups() = changeSelection { groupFilter.toggleFollowingFeatured() }

    fun setFeatured(featured: Boolean, groupName: String) {
        groupFilter.setFeatured(featured, groupName)
        publishGroupFilter()
    }

    suspend fun loadGroupDirectory(forceRefresh: Boolean = false) {
        mutableState.value = current.copy(groupDirectoryErrorMessage = null)
        val repository = groupDirectoryRepository
        if (repository == null) {
            groupFilter.mergeObservedGroups(eventWindow.participatingGroupNames)
            publishGroupFilter()
            return
        }
        runCatchingCancellable { repository.groupDirectory(forceRefresh) }
            .onSuccess { directory ->
                groupFilter.mergeDirectory(
                    groups = directory.groups,
                    revision = directory.revision,
                    observedGroups = eventWindow.participatingGroupNames,
                )
                publishGroupFilter()
            }
            .onFailure { failure ->
                mutableState.value = current.copy(groupDirectoryErrorMessage = failure.userMessage())
            }
    }

    private inline fun changeSelection(change: () -> Unit) {
        val previousSelection = groupFilter.selection
        change()
        if (groupFilter.selection != previousSelection) {
            updateVisibleMonthEvents()
        } else {
            publishGroupFilter()
        }
    }

    // Prefetch window

    private suspend fun restoreCachedSnapshot(ranges: List<DateRange>): Boolean {
        val lookup = cacheReader.lookup(ranges)
        lookup.windowToApply?.let { window ->
            applyPrefetchedWindow(
                from = window.start,
                through = window.end,
                items = window.items,
                sourceStatus = AgendaSourceStatus.ACTIVE,
                fromCache = true,
            )
        }
        return lookup.hasSnapshot
    }

    /** Loads, one month at a time, the months of the window around [containing] not loaded yet. */
    private suspend fun extendPrefetchWindowIfNeeded(containing: LocalDate) {
        val desiredRanges = AgendaCalendarMath.prefetchRanges(containing)
        val missingMonths = AgendaCalendarMath.monthStarts(desiredRanges.first().start, desiredRanges.last().end)
            .filter { month ->
                !eventWindow.containsMonth(month) && AgendaCalendarMath.monthKey(month) !in monthsBeingPrefetched
            }

        for (monthStart in missingMonths) {
            val key = AgendaCalendarMath.monthKey(monthStart)
            val range = AgendaCalendarMath.monthRange(monthStart)
            monthsBeingPrefetched += key
            try {
                val result = pageLoader.fetch(range, forceRefresh = false)
                eventWindow.replace(range.start, range.end, result.items)
                eventWindow.markLoaded(monthStartingAt = monthStart)
                groupFilter.mergeObservedGroups(eventWindow.participatingGroupNames)
                updateVisibleMonthEvents()
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (_: Exception) {
                // The selected month is already loaded. A failed edge extension is
                // retried on a later navigation without interrupting the screen.
            } finally {
                monthsBeingPrefetched -= key
            }
        }
    }

    private fun applyPrefetchedWindow(
        from: LocalDate,
        through: LocalDate,
        items: List<CastellEvent>,
        sourceStatus: AgendaSourceStatus,
        fromCache: Boolean,
    ) {
        eventWindow.replace(from, through, items)
        eventWindow.markLoaded(from, through)
        groupFilter.mergeObservedGroups(eventWindow.participatingGroupNames)
        mutableState.value = current.copy(sourceStatus = sourceStatus, isFromCache = fromCache)
        updateVisibleMonthEvents()
    }

    private fun updateVisibleMonthEvents() {
        val projection = eventWindow.projection(
            selectedDate = current.selectedDate,
            visibleMonth = current.visibleMonth,
            matches = groupFilter::matches,
        )
        mutableState.value = current.copy(
            events = projection.events,
            otherEvents = projection.otherEvents,
            eventDateKeys = projection.eventDateKeys,
            monthEvents = projection.monthEvents,
            groupFilter = groupFilter.snapshot(),
        )
    }

    private fun publishGroupFilter() {
        mutableState.value = current.copy(groupFilter = groupFilter.snapshot())
    }
}
