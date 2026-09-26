package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.agenda.CachedAgendaRepository
import com.ahuguet.castellsenvena.core.data.hourbyhour.CachedHourByHourRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourPage
import com.ahuguet.castellsenvena.core.network.service.AgendaRemoteService
import com.ahuguet.castellsenvena.core.network.service.HourByHourRemoteService
import java.io.IOException
import java.time.Instant
import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest

class CacheRepositoriesTest {
    private val day: LocalDate = LocalDate.of(2026, 7, 21)

    @Test
    fun hourByHourReturnsNetworkItemsThenFallsBackToTheCache() = runTest {
        val remote = SequencedHourByHourRemote()
        val repository = CachedHourByHourRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))

        val fresh = repository.page(cursor = null, limit = 30, forceRefresh = false)
        assertEquals(listOf("Notícia nova"), fresh.items.map { it.title })
        assertNull(fresh.items.single().actionUrl)
        assertFalse(fresh.fromCache)

        val cached = repository.page(cursor = null, limit = 30, forceRefresh = false)
        assertEquals(listOf("Notícia nova"), cached.items.map { it.title })
        assertNull(cached.items.single().actionUrl)
        assertTrue(cached.fromCache)
        assertEquals(fresh.items, cached.items)
    }

    @Test
    fun hourByHourPaginationFailuresAreNotHiddenByTheCache() = runTest {
        val remote = SequencedHourByHourRemote()
        val repository = CachedHourByHourRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))
        repository.page(cursor = null, limit = 30, forceRefresh = false)

        assertFailsWith<IOException> { repository.page(cursor = "page-2", limit = 30, forceRefresh = false) }
    }

    @Test
    fun agendaReadsThePersistedSnapshotWithoutCallingTheRemoteServiceAgain() = runTest {
        val remote = SequencedAgendaRemote()
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))

        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        val cached = repository.cachedEvents(day, day, group = null, municipality = null)

        assertEquals(listOf("Diada de prova"), cached.map { it.title })
        assertEquals(1, remote.calls)
    }

    @Test
    fun agendaReturnsNetworkEventsThenFallsBackToTheSelectedDayCache() = runTest {
        val repository = CachedAgendaRepository(
            SequencedAgendaRemote(),
            inMemoryDatabase(),
            StandardTestDispatcher(testScheduler),
        )

        val fresh = repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        assertEquals(listOf("Diada de prova"), fresh.items.map { it.title })
        assertFalse(fresh.fromCache)

        val cached = repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        assertEquals(listOf("Diada de prova"), cached.items.map { it.title })
        assertTrue(cached.fromCache)
        assertEquals(listOf("Colla A"), cached.items.single().participatingGroups)
    }

    @Test
    fun unavailableSourceDoesNotErasePreviouslyCachedEvents() = runTest {
        val remote = ScriptedAgendaRemote(
            agendaPage(listOf(castellEvent("event-1", "Diada de prova"))),
            agendaPage(emptyList(), status = AgendaSourceStatus.UNAVAILABLE, fromCache = true),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))

        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        val cached = repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)

        assertEquals(listOf("Diada de prova"), cached.items.map { it.title })
        assertTrue(cached.fromCache)
        assertEquals(AgendaSourceStatus.UNAVAILABLE, cached.sourceStatus)
    }

    @Test
    fun unavailableSourceRemovesPreviouslyCachedDemoEvents() = runTest {
        val demo = castellEvent(
            id = "demo",
            title = "Diada de demostració",
            sourceId = "cccc-fixture",
            notes = "Dada simulada per al desenvolupament local.",
        )
        val remote = ScriptedAgendaRemote(
            agendaPage(listOf(demo)),
            agendaPage(emptyList(), status = AgendaSourceStatus.UNAVAILABLE, fromCache = true),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))

        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        val result = repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)

        assertTrue(result.items.isEmpty())
        assertEquals(AgendaSourceStatus.UNAVAILABLE, result.sourceStatus)
    }

    @Test
    fun aCompleteAnswerRemovesCancelledEventsFromTheStoredRange() = runTest {
        val remote = ScriptedAgendaRemote(
            agendaPage(listOf(castellEvent("kept", "Es fa"), castellEvent("cancelled", "Anul·lada"))),
            agendaPage(listOf(castellEvent("kept", "Es fa"))),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))

        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)
        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)

        assertEquals(listOf("kept"), repository.cachedEvents(day, day, null, null).map { it.id })
    }

    @Test
    fun aPagedAnswerReplacesTheStoredRangeOnceItsLastPageArrives() = runTest {
        val remote = ScriptedAgendaRemote(
            agendaPage(listOf(castellEvent("first", "Primera"), castellEvent("cancelled", "Anul·lada"))),
            agendaPage(listOf(castellEvent("first", "Primera")), nextCursor = "page-2"),
            agendaPage(listOf(castellEvent("second", "Segona"))),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))
        repository.events(day, day, null, null, cursor = null, limit = 1, forceRefresh = false)

        repository.events(day, day, null, null, cursor = null, limit = 1, forceRefresh = false)
        assertEquals(
            listOf("cancelled", "first"),
            repository.cachedEvents(day, day, null, null).map { it.id }.sorted(),
        )

        repository.events(day, day, null, null, cursor = "page-2", limit = 1, forceRefresh = false)
        assertEquals(
            listOf("first", "second"),
            repository.cachedEvents(day, day, null, null).map { it.id }.sorted(),
        )
    }

    @Test
    fun aPageWhoseEarlierPagesWereNotSeenKeepsTheStoredRange() = runTest {
        val remote = ScriptedAgendaRemote(
            agendaPage(listOf(castellEvent("first", "Primera"), castellEvent("other", "Una altra"))),
            agendaPage(listOf(castellEvent("second", "Segona"))),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))
        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)

        repository.events(day, day, null, null, cursor = "unknown", limit = 50, forceRefresh = false)

        assertEquals(
            listOf("first", "other", "second"),
            repository.cachedEvents(day, day, null, null).map { it.id }.sorted(),
        )
    }

    @Test
    fun cachedEventsFilterByGroupAndMunicipalityIgnoringCaseAndAccents() = runTest {
        val remote = ScriptedAgendaRemote(
            agendaPage(
                listOf(
                    castellEvent("gracia", "Festa Major", participatingGroups = listOf("Castellers de la Vila de Gràcia")),
                    castellEvent("valls", "Santa Úrsula", municipality = "Valls", participatingGroups = listOf("Colla Vella")),
                    castellEvent("tarragona", "Santa Tecla", municipality = "Tarragona", sourceOrder = 1),
                ),
            ),
        )
        val repository = CachedAgendaRepository(remote, inMemoryDatabase(), StandardTestDispatcher(testScheduler))
        repository.events(day, day, null, null, cursor = null, limit = 50, forceRefresh = false)

        assertEquals(
            listOf("gracia"),
            repository.cachedEvents(day, day, group = "castellers de la vila de GRACIA", municipality = null).map { it.id },
        )
        assertEquals(listOf("tarragona"), repository.cachedEvents(day, day, null, municipality = " tarragona ").map { it.id })
    }

    private class SequencedHourByHourRemote : HourByHourRemoteService {
        private var calls = 0

        override suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage {
            calls += 1
            if (calls > 1) throw offline()
            val now = Instant.parse("2026-07-20T12:45:22Z")
            return HourByHourPage(
                items = listOf(
                    HourByHourItem(
                        id = "1",
                        sourceId = "revista-castells",
                        externalId = "external",
                        title = "Notícia nova",
                        displayTitle = "Notícia nova",
                        summary = "Resum",
                        publishedAt = now,
                        sourceOrder = 0,
                        articleUrl = "https://example.com/article",
                        actionUrl = null,
                        attribution = "Revista Castells",
                        createdAt = now,
                        updatedAt = now,
                    ),
                ),
                nextCursor = null,
                fromCache = false,
            )
        }
    }

    private class SequencedAgendaRemote : AgendaRemoteService {
        var calls = 0

        override suspend fun events(
            from: LocalDate,
            to: LocalDate,
            group: String?,
            municipality: String?,
            cursor: String?,
            limit: Int,
            forceRefresh: Boolean,
        ): AgendaPage {
            calls += 1
            if (calls > 1) throw offline()
            return agendaPage(listOf(castellEvent("event-1", "Diada de prova")))
        }
    }

    private class ScriptedAgendaRemote(vararg pages: AgendaPage) : AgendaRemoteService {
        private val pages = ArrayDeque(pages.toList())

        override suspend fun events(
            from: LocalDate,
            to: LocalDate,
            group: String?,
            municipality: String?,
            cursor: String?,
            limit: Int,
            forceRefresh: Boolean,
        ): AgendaPage = pages.removeFirstOrNull() ?: throw offline()
    }
}
