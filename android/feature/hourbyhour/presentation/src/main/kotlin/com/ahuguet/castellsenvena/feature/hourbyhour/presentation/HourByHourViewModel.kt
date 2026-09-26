package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import com.ahuguet.castellsenvena.core.common.userMessage
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourRepository
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourItemMerger.Policy
import java.time.ZoneId
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlin.time.TimeSource
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive

data class HourByHourState(
    val items: List<HourByHourItem> = emptyList(),
    val dayGroups: List<HourByHourDayGroup> = emptyList(),
    /** Increments when a background check brings items that were not loaded. */
    val newItemsRevision: Int = 0,
    val isLoading: Boolean = false,
    val isLoadingMore: Boolean = false,
    /** The startup screen waits for the first answer, successful or not. */
    val hasCompletedInitialLoad: Boolean = false,
    val isFromCache: Boolean = false,
    val errorMessage: String? = null,
)

/**
 * The Hora a Hora feed: first load, pull to refresh, pagination and the
 * periodic background check while the section is visible.
 */
class HourByHourViewModel(
    private val repository: HourByHourRepository,
    private val zone: () -> ZoneId = ZoneId::systemDefault,
    private val sleep: suspend (Duration) -> Unit = { delay(it) },
    private val timeSource: TimeSource = TimeSource.Monotonic,
) {
    private val mutableState = MutableStateFlow(HourByHourState())
    val state: StateFlow<HourByHourState> = mutableState.asStateFlow()

    private var nextCursor: String? = null

    suspend fun loadIfNeeded() {
        val current = mutableState.value
        if (current.items.isNotEmpty() || current.isLoading) return
        load(forceRefresh = false, mergePolicy = Policy.REPLACE)
        mutableState.update { it.copy(hasCompletedInitialLoad = true) }
    }

    /** Stays busy long enough for the pull-to-refresh gesture to register. */
    suspend fun refresh() {
        val startedAt = timeSource.markNow()
        load(forceRefresh = true, mergePolicy = Policy.REPLACE)
        val remaining = MINIMUM_REFRESH_DURATION - startedAt.elapsedNow()
        if (remaining.isPositive()) delay(remaining)
    }

    suspend fun revalidate() {
        load(forceRefresh = false, mergePolicy = Policy.REVALIDATE)
    }

    /** Runs until cancelled: checks for new items every [interval]. */
    suspend fun runAutoRefresh(interval: Duration = 60.seconds) {
        if (mutableState.value.items.isEmpty()) loadIfNeeded() else revalidate()
        while (currentCoroutineContext().isActive) {
            try {
                sleep(interval)
            } catch (_: Exception) {
                return
            }
            if (!currentCoroutineContext().isActive) return
            revalidate()
        }
    }

    suspend fun loadNextIfNeeded(after: HourByHourItem) {
        val current = mutableState.value
        val cursor = nextCursor
        if (after.id != current.items.lastOrNull()?.id ||
            cursor == null ||
            current.isLoading ||
            current.isLoadingMore
        ) {
            return
        }
        mutableState.update { it.copy(isLoadingMore = true) }
        try {
            val page = repository.page(cursor = cursor, limit = PAGE_SIZE, forceRefresh = false)
            merge(page.items, Policy.APPEND)
            nextCursor = page.nextCursor
            mutableState.update { it.copy(isFromCache = page.fromCache) }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            mutableState.update { it.copy(errorMessage = failure.userMessage()) }
        } finally {
            mutableState.update { it.copy(isLoadingMore = false) }
        }
    }

    private suspend fun load(forceRefresh: Boolean, mergePolicy: Policy) {
        val current = mutableState.value
        if (current.isLoading || current.isLoadingMore) return
        mutableState.update { it.copy(isLoading = true, errorMessage = null) }
        try {
            val page = repository.page(cursor = null, limit = PAGE_SIZE, forceRefresh = forceRefresh)
            // A revalidation keeps the pagination already loaded below the fresh page.
            val shouldAdoptFreshCursor = nextCursor == null
            merge(page.items, mergePolicy)
            if (mergePolicy == Policy.REPLACE || shouldAdoptFreshCursor) nextCursor = page.nextCursor
            mutableState.update { it.copy(isFromCache = page.fromCache) }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            mutableState.update { it.copy(errorMessage = failure.userMessage()) }
        } finally {
            mutableState.update { it.copy(isLoading = false) }
        }
    }

    private fun merge(incoming: List<HourByHourItem>, policy: Policy) {
        val current = mutableState.value
        val result = HourByHourItemMerger.merge(incoming, current.items, policy)
        if (result.items == current.items) return
        val dayGroups = HourByHourDayGrouping.groups(result.items, zone())
        mutableState.update {
            it.copy(
                items = result.items,
                dayGroups = dayGroups,
                newItemsRevision = if (result.containsNewItems) it.newItemsRevision + 1 else it.newItemsRevision,
            )
        }
    }

    private companion object {
        const val PAGE_SIZE = 30
        val MINIMUM_REFRESH_DURATION = 500.milliseconds
    }
}
