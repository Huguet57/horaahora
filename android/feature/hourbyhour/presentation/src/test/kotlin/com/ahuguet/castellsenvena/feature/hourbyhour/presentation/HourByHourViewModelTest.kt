@file:OptIn(ExperimentalCoroutinesApi::class)

package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import java.time.Duration as JavaDuration
import java.time.ZoneId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertSame
import kotlin.test.assertTrue
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

class HourByHourViewModelTest {
    private val zone = ZoneId.of("Europe/Madrid")

    private fun model(repository: com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourRepository) =
        HourByHourViewModel(repository, zone = { zone })

    @Test
    fun initialLoadCompletesOnlyAfterTheRepositoryReturns() = runTest {
        val repository = SuspendingHourByHourRepository(page(listOf(item("first"))))
        val model = model(repository)
        assertFalse(model.state.value.hasCompletedInitialLoad)

        val initialLoad = launch { model.loadIfNeeded() }
        runCurrent()
        assertEquals(1, repository.requests.size)
        assertFalse(model.state.value.hasCompletedInitialLoad)

        repository.resume()
        initialLoad.join()
        assertTrue(model.state.value.hasCompletedInitialLoad)
    }

    @Test
    fun initialLoadCompletesAfterAnError() = runTest {
        val model = model(SequencedHourByHourRepository(emptyList()))

        model.loadIfNeeded()

        assertTrue(model.state.value.hasCompletedInitialLoad)
        assertNotNull(model.state.value.errorMessage)
    }

    @Test
    fun refreshStaysVisibleLongEnoughToAcknowledgeTheGesture() = runTest {
        val repository = SequencedHourByHourRepository(listOf(page(emptyList())))
        val model = HourByHourViewModel(repository, zone = { zone }, timeSource = testScheduler.timeSource)
        val startedAt = currentTime

        model.refresh()

        assertTrue(currentTime - startedAt >= 450)
        assertEquals(listOf(true), repository.requests.map { it.forceRefresh })
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun autoRefreshLoadsThenRevalidatesWithoutForcingTheSource() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(page(listOf(item("first"))), page(listOf(item("second"), item("first")))),
        )
        val sleeper = SequencedSleeper(successfulSleeps = 1)
        val model = HourByHourViewModel(repository, zone = { zone }, sleep = sleeper::sleep)

        model.runAutoRefresh(interval = 60.seconds)

        assertEquals(listOf(false, false), repository.requests.map { it.forceRefresh })
        assertEquals(listOf(60.seconds, 60.seconds), sleeper.durations)
        assertEquals(listOf("second", "first"), model.state.value.items.map { it.id })
    }

    @Test
    fun autoRefreshRevalidatesImmediatelyWhenContentIsAlreadyLoaded() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(page(listOf(item("first"))), page(listOf(item("second"), item("first")))),
        )
        val model = HourByHourViewModel(repository, zone = { zone }, sleep = SequencedSleeper(0)::sleep)
        model.loadIfNeeded()

        model.runAutoRefresh(interval = 60.seconds)

        assertEquals(listOf(false, false), repository.requests.map { it.forceRefresh })
        assertEquals(listOf("second", "first"), model.state.value.items.map { it.id })
    }

    @Test
    fun revalidationUpdatesEntriesWithoutDiscardingPagination() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(
                page(listOf(item("newest"), item("middle", title = "Original")), nextCursor = "page-2"),
                page(listOf(item("old")), nextCursor = "page-3"),
                page(
                    listOf(item("brand-new"), item("newest"), item("middle", title = "Actualitzat")),
                    nextCursor = "fresh-page-2",
                ),
                page(listOf(item("oldest"))),
            ),
        )
        val model = model(repository)

        model.loadIfNeeded()
        model.loadNextIfNeeded(after = model.state.value.items.last())
        model.revalidate()

        assertEquals(listOf("brand-new", "newest", "middle", "old"), model.state.value.items.map { it.id })
        assertEquals("Actualitzat", model.state.value.items.first { it.id == "middle" }.title)

        model.loadNextIfNeeded(after = model.state.value.items.last())

        assertEquals(listOf(null, "page-2", null, "page-3"), repository.requests.map { it.cursor })
        assertEquals(listOf("brand-new", "newest", "middle", "old", "oldest"), model.state.value.items.map { it.id })
    }

    @Test
    fun paginationOnlyStartsFromTheLastItem() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(page(listOf(item("first"), item("second")), nextCursor = "page-2"), page(listOf(item("third")))),
        )
        val model = model(repository)
        model.loadIfNeeded()

        model.loadNextIfNeeded(after = model.state.value.items.first())
        assertEquals(1, repository.requests.size)

        model.loadNextIfNeeded(after = model.state.value.items.last())
        model.loadNextIfNeeded(after = model.state.value.items.last())
        assertEquals(listOf(null, "page-2"), repository.requests.map { it.cursor })
    }

    @Test
    fun dayGroupsKeepTheirIdentityWhenANewerDayIsInserted() = runTest {
        val olderDate = defaultTimestamp
        val newerDate = olderDate.plus(JavaDuration.ofDays(1))
        val repository = SequencedHourByHourRepository(
            listOf(
                page(listOf(item("older", publishedAt = olderDate))),
                page(listOf(item("newer", publishedAt = newerDate), item("older", publishedAt = olderDate))),
            ),
        )
        val model = model(repository)

        model.loadIfNeeded()
        val originalId = model.state.value.dayGroups.first().id
        model.revalidate()

        val olderGroup = model.state.value.dayGroups.first { group -> group.items.any { it.id == "older" } }
        assertEquals(originalId, olderGroup.id)
        assertEquals(2, model.state.value.dayGroups.size)
    }

    @Test
    fun dayGroupsTrackItemsAddedByPagination() = runTest {
        val firstDate = defaultTimestamp
        val secondDate = firstDate.minus(JavaDuration.ofDays(1))
        val repository = SequencedHourByHourRepository(
            listOf(
                page(listOf(item("first", publishedAt = firstDate)), nextCursor = "page-2"),
                page(listOf(item("second", publishedAt = secondDate))),
            ),
        )
        val model = model(repository)

        model.loadIfNeeded()
        model.loadNextIfNeeded(after = model.state.value.items.last())

        assertEquals(2, model.state.value.dayGroups.size)
        assertEquals(listOf("first", "second"), model.state.value.dayGroups.flatMap { it.items }.map { it.id })
    }

    @Test
    fun identicalRevalidationDoesNotPublishNewDayGroups() = runTest {
        val unchangedItems = listOf(item("first"))
        val repository = SequencedHourByHourRepository(listOf(page(unchangedItems), page(unchangedItems)))
        val model = model(repository)
        model.loadIfNeeded()
        val dayGroups = model.state.value.dayGroups

        model.revalidate()

        assertSame(dayGroups, model.state.value.dayGroups)
    }

    @Test
    fun revalidationDoesNotOverlapAnInFlightLoad() = runTest {
        val repository = SuspendingHourByHourRepository(page(listOf(item("first"))))
        val model = model(repository)

        val initialLoad = launch { model.loadIfNeeded() }
        runCurrent()
        model.revalidate()

        assertEquals(1, repository.requests.size)
        repository.resume()
        initialLoad.join()
    }

    @Test
    fun autoRefreshStopsWhenItsJobIsCancelled() = runTest {
        val repository = SequencedHourByHourRepository(listOf(page(listOf(item("first")))))
        var sleeping = false
        val model = HourByHourViewModel(
            repository,
            zone = { zone },
            sleep = { duration ->
                sleeping = true
                delay(duration)
            },
        )

        val refresh = launch { model.runAutoRefresh(interval = 60.seconds) }
        runCurrent()
        assertTrue(sleeping)
        refresh.cancel()
        refresh.join()

        assertEquals(1, repository.requests.size)
    }

    @Test
    fun revalidationRevisesNewItemsOnlyForAnUnknownIdentity() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(
                page(listOf(item("first", title = "Original"))),
                page(listOf(item("first", title = "Original"))),
                page(listOf(item("first", title = "Actualitzat"))),
                page(listOf(item("second"), item("first", title = "Actualitzat"))),
            ),
        )
        val model = model(repository)

        model.loadIfNeeded()
        assertEquals(0, model.state.value.newItemsRevision)
        model.revalidate()
        assertEquals(0, model.state.value.newItemsRevision)
        model.revalidate()
        assertEquals(0, model.state.value.newItemsRevision)
        model.revalidate()
        assertEquals(1, model.state.value.newItemsRevision)
    }

    @Test
    fun paginationDoesNotReviseNewItems() = runTest {
        val repository = SequencedHourByHourRepository(
            listOf(page(listOf(item("first")), nextCursor = "page-2"), page(listOf(item("older")))),
        )
        val model = model(repository)

        model.loadIfNeeded()
        model.loadNextIfNeeded(after = model.state.value.items.last())

        assertEquals(0, model.state.value.newItemsRevision)
    }
}
