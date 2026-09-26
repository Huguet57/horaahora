@file:OptIn(ExperimentalCoroutinesApi::class)

package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

class AgendaViewModelTest {
    private fun model(repository: AgendaRepositoryStub, selected: String) =
        AgendaViewModel(repository, today = agendaDate(selected))

    @Test
    fun loadPrefetchesSixMonthsBeforeAndAfterTheVisibleMonth() = runTest {
        val repository = AgendaRepositoryStub()
        val model = model(repository, "2026-07-21")

        model.load()

        val state = model.state.value
        assertEquals(listOf("Diada nativa"), state.events.map { it.title })
        assertEquals(setOf("2026-07-21", "2026-07-22"), state.eventDateKeys)
        assertEquals(AgendaSourceStatus.ACTIVE, state.sourceStatus)
        assertEquals(100, repository.requestedLimit)
        assertEquals(
            listOf("2026-01-01|2026-07-31", "2026-08-01|2027-01-31"),
            repository.requests.map { "${it.from}|${it.to}" },
        )
    }

    @Test
    fun forceRefreshRefetchesTheWholePrefetchWindow() = runTest {
        val repository = AgendaRepositoryStub()
        val model = model(repository, "2026-07-21")
        model.load()

        model.load(forceRefresh = true)

        assertEquals(4, repository.requests.size)
        assertEquals(listOf(false, false), repository.requests.take(2).map { it.forceRefresh })
        assertEquals(listOf(true, true), repository.requests.takeLast(2).map { it.forceRefresh })
    }

    @Test
    fun refreshKeepsCurrentEventsVisibleAndOnlyReloadsTheVisibleMonth() = runTest {
        val original = makeAgendaEvent(id = "original", localDate = "2026-07-21", title = "Diada desada")
        val updated = makeAgendaEvent(id = "updated", localDate = "2026-07-21", title = "Diada actualitzada")
        val neighboringMonth = makeAgendaEvent(id = "august", localDate = "2026-08-01", title = "Diada d'agost")
        val repository = AgendaRepositoryStub(suppliedItems = listOf(original, neighboringMonth))
        val model = model(repository, "2026-07-21")
        model.load()
        repository.suspendNextForcedRefresh()

        val refresh = launch { model.refresh() }
        runCurrent()
        assertTrue(repository.hasSuspendedRequest)

        assertEquals(listOf("Diada desada"), model.state.value.events.map { it.title })
        assertEquals(setOf("2026-07-21", "2026-08-01"), model.state.value.eventDateKeys)
        assertEquals(3, repository.requests.size)
        assertEquals(AgendaRepositoryStub.Request("2026-07-01", "2026-07-31", true), repository.requests.last())

        repository.resumeSuspendedRequest(listOf(updated))
        refresh.join()

        assertEquals(listOf("Diada actualitzada"), model.state.value.events.map { it.title })
        assertEquals(setOf("2026-07-21", "2026-08-01"), model.state.value.eventDateKeys)
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun refreshDoesNotOverlapAnInFlightAgendaLoad() = runTest {
        val repository = AgendaRepositoryStub()
        val model = model(repository, "2026-07-21")
        repository.suspendNextRequest()

        val initialLoad = launch { model.load() }
        runCurrent()
        assertTrue(repository.hasSuspendedRequest)
        val requestsBeforeRefresh = repository.requests.size

        model.refresh()

        assertEquals(requestsBeforeRefresh, repository.requests.size)
        assertFalse(repository.requests.any { it.forceRefresh })
        repository.resumeSuspendedRequest()
        initialLoad.join()
    }

    @Test
    fun loadKeepsTheCachedSnapshotWhenSilentRevalidationFails() = runTest {
        val cachedEvent = makeAgendaEvent(id = "cached", localDate = "2026-07-21", title = "Desada al dispositiu")
        val repository = AgendaRepositoryStub(suppliedCachedItems = listOf(cachedEvent), remoteError = offline())
        val model = model(repository, "2026-07-21")

        model.load()

        assertEquals(listOf("Desada al dispositiu"), model.state.value.events.map { it.title })
        assertTrue(model.state.value.isFromCache)
        assertNull(model.state.value.errorMessage)
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun loadWithoutAnySnapshotShowsTheError() = runTest {
        val model = model(AgendaRepositoryStub(remoteError = offline()), "2026-07-21")

        model.load()

        assertEquals("S'ha produït un error inesperat.", model.state.value.errorMessage)
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun preloadFromCacheHydratesTheAgendaWithoutStartingARequest() = runTest {
        val cachedEvent = makeAgendaEvent(id = "cached", localDate = "2026-07-21", title = "Desada al dispositiu")
        val repository = AgendaRepositoryStub(suppliedCachedItems = listOf(cachedEvent))
        val model = model(repository, "2026-07-21")

        model.preloadFromCache()

        val state = model.state.value
        assertEquals(listOf("Desada al dispositiu"), state.events.map { it.title })
        assertEquals(listOf("Desada al dispositiu"), state.monthEvents.map { it.title })
        assertEquals(AgendaSourceStatus.ACTIVE, state.sourceStatus)
        assertTrue(state.isFromCache)
        assertFalse(state.isLoading)
        assertTrue(repository.requests.isEmpty())
    }

    @Test
    fun loadReusesThePreloadedSnapshotWithoutReadingTheSameCacheWindowAgain() = runTest {
        val cachedEvent = makeAgendaEvent(id = "cached", localDate = "2026-07-21", title = "Desada al dispositiu")
        val repository = AgendaRepositoryStub(suppliedCachedItems = listOf(cachedEvent), remoteError = offline())
        val model = model(repository, "2026-07-21")
        model.preloadFromCache()

        model.load()

        assertEquals(2, repository.cachedRequests.size)
        assertEquals(listOf("Desada al dispositiu"), model.state.value.events.map { it.title })
        assertNull(model.state.value.errorMessage)
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun prefetchDeduplicatesEventsAndKeepsMonthEventsScopedToTheMonth() = runTest {
        val repository = AgendaRepositoryStub(
            suppliedItems = listOf(
                makeAgendaEvent(id = "june", localDate = "2026-06-30", title = "Juny"),
                makeAgendaEvent(id = "july", localDate = "2026-07-21", title = "Juliol"),
                makeAgendaEvent(id = "july", localDate = "2026-07-21", title = "Duplicada"),
                makeAgendaEvent(id = "august", localDate = "2026-08-01", title = "Agost"),
            ),
        )
        val model = model(repository, "2026-07-21")

        model.load()

        assertEquals(listOf("Juliol"), model.state.value.monthEvents.map { it.title })
        assertEquals(setOf("2026-06-30", "2026-07-21", "2026-08-01"), model.state.value.eventDateKeys)
        assertEquals(listOf("Juliol"), model.state.value.events.map { it.title })
    }

    @Test
    fun selectingADayInAnotherMonthUsesPrefetchedDataAndExtendsTheWindow() = runTest {
        val repository = AgendaRepositoryStub(
            suppliedItems = listOf(
                makeAgendaEvent(id = "july", localDate = "2026-07-31", title = "Juliol"),
                makeAgendaEvent(id = "august", localDate = "2026-08-01", title = "Agost"),
            ),
        )
        val model = model(repository, "2026-07-31")
        model.load()

        model.selectAndLoad(agendaDate("2026-08-01"))

        assertEquals(3, repository.requests.size)
        assertEquals("2027-02-01", repository.requests.last().from)
        assertEquals("2027-02-28", repository.requests.last().to)
        assertEquals(listOf("Agost"), model.state.value.events.map { it.title })
        assertEquals(listOf("Agost"), model.state.value.monthEvents.map { it.title })
        assertFalse(model.state.value.isLoading)

        model.selectAndLoad(agendaDate("2026-08-02"))
        assertEquals(3, repository.requests.size)
    }

    @Test
    fun changingWeekKeepsTheActiveDayAndExtendsThePrefetchWindowInTheBackground() = runTest {
        val repository = AgendaRepositoryStub()
        val model = model(repository, "2026-07-28")
        model.load()

        model.changeWeek(1)

        assertEquals(LocalDate.parse("2026-07-28"), model.state.value.selectedDate)
        assertEquals(LocalDate.parse("2026-08-04"), model.state.value.visibleWeek)
        assertEquals(3, repository.requests.size)
        assertEquals("2027-02-01", repository.requests.last().from)
        assertEquals("2027-02-28", repository.requests.last().to)
        assertFalse(model.state.value.isLoading)
    }

    @Test
    fun changingMonthKeepsTheActiveDayAndExtendsThePrefetchWindow() = runTest {
        val repository = AgendaRepositoryStub(
            suppliedItems = listOf(
                makeAgendaEvent(id = "december", localDate = "2026-12-21", title = "Desembre"),
                makeAgendaEvent(id = "january", localDate = "2027-01-21", title = "Gener"),
            ),
        )
        val model = model(repository, "2026-12-21")
        model.load()

        model.changeMonth(1)

        assertEquals(LocalDate.parse("2026-12-21"), model.state.value.selectedDate)
        assertEquals(LocalDate.parse("2027-01-21"), model.state.value.visibleMonth)
        assertEquals(listOf("Desembre"), model.state.value.events.map { it.title })
        assertEquals(listOf("Gener"), model.state.value.monthEvents.map { it.title })
        assertEquals(3, repository.requests.size)
        assertEquals("2027-07-01", repository.requests.last().from)
        assertEquals("2027-07-31", repository.requests.last().to)
    }
}
