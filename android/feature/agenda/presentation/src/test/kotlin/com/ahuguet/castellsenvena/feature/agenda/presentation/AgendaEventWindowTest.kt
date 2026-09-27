package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.DateRange
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaEventWindow
import com.ahuguet.castellsenvena.feature.agenda.presentation.events.AgendaPageLoader
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupCatalog
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupNameNormalizer
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaOtherEventsDisclosureState
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.groupMatchesSearch
import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class AgendaEventWindowTest {
    @Test
    fun replacingARangeDeduplicatesSortsAndPreservesNeighboringEvents() {
        val window = AgendaEventWindow()
        window.replace(
            agendaDate("2026-06-01"),
            agendaDate("2026-08-31"),
            listOf(
                makeAgendaEvent(id = "august", localDate = "2026-08-01", title = "August"),
                makeAgendaEvent(id = "july", localDate = "2026-07-21", title = "July"),
                makeAgendaEvent(id = "july", localDate = "2026-07-21", title = "Duplicate"),
            ),
        )

        window.replace(
            agendaDate("2026-07-01"),
            agendaDate("2026-07-31"),
            listOf(makeAgendaEvent(id = "updated", localDate = "2026-07-22", title = "Updated")),
        )

        assertEquals(setOf("2026-07-22", "2026-08-01"), window.dateKeys)
        assertEquals(listOf("updated"), window.eventsOn(agendaDate("2026-07-22")).map { it.externalId })
    }

    @Test
    fun eventsInMonthExcludePrefetchedNeighboringMonths() {
        val window = AgendaEventWindow()
        window.replace(
            agendaDate("2026-06-01"),
            agendaDate("2026-08-31"),
            listOf(
                makeAgendaEvent(id = "june", localDate = "2026-06-30", title = "June"),
                makeAgendaEvent(id = "july", localDate = "2026-07-21", title = "July"),
                makeAgendaEvent(id = "august", localDate = "2026-08-01", title = "August"),
            ),
        )

        assertEquals(listOf("july"), window.eventsInMonth(agendaDate("2026-07-15")).map { it.externalId })
    }

    @Test
    fun loadedMonthsAreTrackedIndependentlyFromTheirEvents() {
        val window = AgendaEventWindow()

        window.markLoaded(agendaDate("2026-06-01"), agendaDate("2026-08-31"))

        assertTrue(window.containsMonth(agendaDate("2026-06-15")))
        assertTrue(window.containsMonth(agendaDate("2026-07-15")))
        assertTrue(window.containsMonth(agendaDate("2026-08-15")))
        assertFalse(window.containsMonth(agendaDate("2026-09-15")))
        assertTrue(window.isEmpty)
    }

    @Test
    fun projectionUsesNormalizedGroupIndexesToPartitionTheDayAndMonth() {
        val window = AgendaEventWindow()
        window.replace(
            agendaDate("2026-07-01"),
            agendaDate("2026-08-31"),
            listOf(
                makeAgendaEvent("selected-day", "2026-07-25", "Selected day", participatingGroups = listOf("Castellers de la Vila de Gràcia")),
                makeAgendaEvent("other-day", "2026-07-25", "Other day", participatingGroups = listOf("Colla B")),
                makeAgendaEvent("without-groups", "2026-07-25", "Without groups", participatingGroups = emptyList()),
                makeAgendaEvent("selected-month", "2026-07-26", "Selected month", participatingGroups = listOf("Castellers de la Vila de Gràcia")),
                makeAgendaEvent("selected-next-month", "2026-08-01", "Next month", participatingGroups = listOf("Castellers de la Vila de Gràcia")),
            ),
        )
        val selectedKeys = setOf("castellers de la vila de gracia")

        val projection = window.projection(agendaDate("2026-07-25"), agendaDate("2026-07-15")) { keys ->
            keys.any { it in selectedKeys }
        }

        assertEquals(listOf("selected-day"), projection.events.map { it.externalId })
        assertEquals(listOf("other-day", "without-groups"), projection.otherEvents.map { it.externalId })
        assertEquals(setOf("2026-07-25", "2026-07-26", "2026-08-01"), projection.eventDateKeys)
        assertEquals(listOf("selected-day", "selected-month"), projection.monthEvents.map { it.externalId })
    }

    @Test
    fun projectionIncludesDatesWithNoGroupsWhenEveryEventMatches() {
        val window = AgendaEventWindow()
        window.replace(
            agendaDate("2026-07-01"),
            agendaDate("2026-07-31"),
            listOf(makeAgendaEvent("without-groups", "2026-07-27", "Without groups", participatingGroups = emptyList())),
        )

        val projection = window.projection(agendaDate("2026-07-27"), agendaDate("2026-07-15")) { true }

        assertEquals(listOf("without-groups"), projection.events.map { it.externalId })
        assertTrue(projection.otherEvents.isEmpty())
        assertEquals(setOf("2026-07-27"), projection.eventDateKeys)
        assertEquals(listOf("without-groups"), projection.monthEvents.map { it.externalId })
    }

    @Test
    fun pageLoaderLoadsEveryPageAndOnlyForcesTheFirstRequest() = runTest {
        val repository = PaginatedAgendaRepository()

        val result = AgendaPageLoader(repository)
            .fetch(DateRange(agendaDate("2026-07-01"), agendaDate("2026-07-31")), forceRefresh = true)

        assertEquals(listOf("first", "second"), result.items.map { it.externalId })
        assertEquals(listOf(null, "next"), repository.requests.map { it.first })
        assertEquals(listOf(true, false), repository.requests.map { it.second })
        assertFalse(result.fromCache)
        assertEquals(AgendaSourceStatus.UNAVAILABLE, result.sourceStatus)
    }

    @Test
    fun catalogMergesDisplayNamesAndKeepsTheirNormalizedKeys() {
        val catalog = AgendaGroupCatalog(
            preferred = listOf("Colla A"),
            fallback = listOf("Castellers de la Vila de Gràcia", "CASTELLERS DE LA VILA DE GRACIA"),
        )

        assertEquals(listOf("Castellers de la Vila de Gràcia", "Colla A"), catalog.names)
        assertEquals(setOf("castellers de la vila de gracia", "colla a"), catalog.keys)
    }

    @Test
    fun groupKeysIgnoreCaseAccentsWhitespaceAndApostropheVariants() {
        assertEquals(
            AgendaGroupNameNormalizer.key("castellers d'altafulla"),
            AgendaGroupNameNormalizer.key("  Castellers   d’Àltafulla "),
        )
        assertTrue(groupMatchesSearch("Castellers de la Vila de Gràcia", "GRACIA"))
        assertFalse(groupMatchesSearch("Castellers de la Vila de Gràcia", "Valls"))
    }

    @Test
    fun otherEventsStartCollapsedOnlyWhenTheDayHasMatchingEvents() {
        assertFalse(AgendaOtherEventsDisclosureState.initial(hasMatchingEvents = true).isExpanded)
        assertTrue(AgendaOtherEventsDisclosureState.initial(hasMatchingEvents = false).isExpanded)
        assertTrue(AgendaOtherEventsDisclosureState.initial(hasMatchingEvents = true).toggled().isExpanded)
    }

    private class PaginatedAgendaRepository : AgendaRepository {
        override val officialUrl = OFFICIAL_URL
        val requests = mutableListOf<Pair<String?, Boolean>>()

        override suspend fun events(
            from: LocalDate,
            to: LocalDate,
            group: String?,
            municipality: String?,
            cursor: String?,
            limit: Int,
            forceRefresh: Boolean,
        ): AgendaPage {
            requests += cursor to forceRefresh
            return if (cursor == null) {
                page(makeAgendaEvent("first", "2026-07-01", "First"), "next", fromCache = true, AgendaSourceStatus.ACTIVE)
            } else {
                page(makeAgendaEvent("second", "2026-07-02", "Second"), null, fromCache = false, AgendaSourceStatus.UNAVAILABLE)
            }
        }

        private fun page(event: CastellEvent, next: String?, fromCache: Boolean, status: AgendaSourceStatus) =
            AgendaPage(listOf(event), next, OFFICIAL_URL, fromCache, status)
    }
}
