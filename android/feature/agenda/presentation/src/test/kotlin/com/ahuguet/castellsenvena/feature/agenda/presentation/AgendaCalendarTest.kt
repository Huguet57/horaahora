package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarFold
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarPaging
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.DateRange
import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class AgendaCalendarTest {
    @Test
    fun monthWeekRowsCoverFourFiveAndSixWeekMonths() {
        val february2027 = AgendaCalendarMath.monthWeekRows(agendaDate("2027-02-11"))
        assertEquals(4, february2027.size)
        assertTrue(february2027.all { it.size == 7 })
        assertEquals("2027-02-01", february2027.first().first().toString())
        assertEquals("2027-02-28", february2027.last().last().toString())

        val july2026 = AgendaCalendarMath.monthWeekRows(agendaDate("2026-07-21"))
        assertEquals(5, july2026.size)
        assertEquals("2026-06-29", july2026.first().first().toString())
        assertEquals("2026-08-02", july2026.last().last().toString())

        val august2026 = AgendaCalendarMath.monthWeekRows(agendaDate("2026-08-15"))
        assertEquals(6, august2026.size)
        assertEquals("2026-07-27", august2026.first().first().toString())
        assertEquals("2026-09-06", august2026.last().last().toString())
    }

    @Test
    fun weekRowIndexFindsTheRowOfTheSelectedDayIncludingAdjacentMonthDays() {
        val july2026 = AgendaCalendarMath.monthWeekRows(agendaDate("2026-07-21"))

        assertEquals(3, AgendaCalendarMath.weekRowIndex(agendaDate("2026-07-21"), july2026))
        assertEquals(1, AgendaCalendarMath.weekRowIndex(agendaDate("2026-07-06"), july2026))
        assertEquals(0, AgendaCalendarMath.weekRowIndex(agendaDate("2026-06-30"), july2026))
        assertEquals(4, AgendaCalendarMath.weekRowIndex(agendaDate("2026-08-01"), july2026))
        assertNull(AgendaCalendarMath.weekRowIndex(agendaDate("2026-12-21"), july2026))
    }

    @Test
    fun monthWeekRowCountMatchesTheGeneratedGridAcrossSeveralYears() {
        for (year in 2025..2028) {
            for (month in 1..12) {
                val referenceDate = LocalDate.of(year, month, 15)
                assertEquals(
                    AgendaCalendarMath.monthWeekRows(referenceDate).size,
                    AgendaCalendarMath.monthWeekRowCount(referenceDate),
                    "Unexpected week-row count for $year-$month",
                )
            }
        }
    }

    @Test
    fun weekStartsOnMondayAndCanCrossTheYearBoundary() {
        val dates = AgendaCalendarMath.week(agendaDate("2027-01-01"))

        assertEquals(
            listOf("2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31", "2027-01-01", "2027-01-02", "2027-01-03"),
            dates.map(LocalDate::toString),
        )
    }

    @Test
    fun prefetchRangesCoverSixMonthsAroundTheVisibleMonth() {
        assertEquals(
            listOf(
                DateRange(agendaDate("2026-01-01"), agendaDate("2026-07-31")),
                DateRange(agendaDate("2026-08-01"), agendaDate("2027-01-31")),
            ),
            AgendaCalendarMath.prefetchRanges(agendaDate("2026-07-21")),
        )
        assertEquals(
            DateRange(agendaDate("2028-02-01"), agendaDate("2028-02-29")),
            AgendaCalendarMath.monthRange(agendaDate("2028-02-10")),
        )
    }

    @Test
    fun catalanCalendarLabelsKeepTheExistingCopy() {
        val july = agendaDate("2026-07-25")

        assertEquals("juliol del 2026", AgendaCalendarMath.monthTitle(july))
        assertEquals("dissabte, 25 de juliol del 2026", AgendaCalendarMath.accessibilityDate(july))
        assertEquals("2026-07", AgendaCalendarMath.monthKey(july))
    }

    @Test
    fun foldDistanceAndGridHeightsForFourFiveAndSixWeekMonths() {
        assertEquals(68f, AgendaCalendarFold.COLLAPSED_GRID_HEIGHT)
        assertEquals(224f, AgendaCalendarFold.expandedGridHeight(4))
        assertEquals(276f, AgendaCalendarFold.expandedGridHeight(5))
        assertEquals(328f, AgendaCalendarFold.expandedGridHeight(6))
        assertEquals(156f, AgendaCalendarFold.foldDistance(4))
        assertEquals(208f, AgendaCalendarFold.foldDistance(5))
        assertEquals(260f, AgendaCalendarFold.foldDistance(6))
        assertEquals(260f, AgendaCalendarFold.MAXIMUM_FOLD_DISTANCE)
    }

    @Test
    fun gridHeightInterpolatesBetweenExpandedAndCollapsed() {
        assertEquals(276f, AgendaCalendarFold.gridHeight(5, progress = 0f))
        assertEquals(68f, AgendaCalendarFold.gridHeight(5, progress = 1f))
        assertEquals(172f, AgendaCalendarFold.gridHeight(5, progress = 0.5f))
        assertEquals(52f, AgendaCalendarFold.inactiveWeekRowSlotHeight(progress = 0f))
        assertEquals(26f, AgendaCalendarFold.inactiveWeekRowSlotHeight(progress = 0.5f))
        assertEquals(0f, AgendaCalendarFold.inactiveWeekRowSlotHeight(progress = 1f))
    }

    @Test
    fun progressIsClampedBetweenZeroAndOne() {
        assertEquals(0f, AgendaCalendarFold.progress(scrollOffset = -40f, foldDistance = 208f))
        assertEquals(0f, AgendaCalendarFold.progress(scrollOffset = 0f, foldDistance = 208f))
        assertEquals(0.5f, AgendaCalendarFold.progress(scrollOffset = 104f, foldDistance = 208f), 0.0001f)
        assertEquals(1f, AgendaCalendarFold.progress(scrollOffset = 208f, foldDistance = 208f))
        assertEquals(1f, AgendaCalendarFold.progress(scrollOffset = 600f, foldDistance = 208f))
        assertEquals(0f, AgendaCalendarFold.progress(scrollOffset = 100f, foldDistance = 0f))
    }

    @Test
    fun reduceMotionUsesDirectStateChangesInsteadOfInterpolation() {
        assertEquals(0.3f, AgendaCalendarFold.effectiveProgress(0.3f, reduceMotion = false))
        assertEquals(0f, AgendaCalendarFold.effectiveProgress(0.3f, reduceMotion = true))
        assertEquals(1f, AgendaCalendarFold.effectiveProgress(0.5f, reduceMotion = true))
        assertEquals(1f, AgendaCalendarFold.effectiveProgress(0.8f, reduceMotion = true))
    }

    @Test
    fun releasingAtHalfTheFoldOrMoreSettlesFolded() {
        assertFalse(AgendaCalendarFold.snapsCollapsed(0f))
        assertFalse(AgendaCalendarFold.snapsCollapsed(0.499f))
        assertTrue(AgendaCalendarFold.snapsCollapsed(0.5f))
        assertTrue(AgendaCalendarFold.snapsCollapsed(1f))
        assertEquals(0f, AgendaCalendarFold.restingProgress(0.3f))
        assertEquals(1f, AgendaCalendarFold.restingProgress(0.7f))
    }

    @Test
    fun snapTargetOffsetOnlyAdjustsTargetsInsideTheFoldZone() {
        assertEquals(0f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 103f, foldDistance = 208f))
        assertEquals(208f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 104f, foldDistance = 208f))
        assertEquals(208f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 207f, foldDistance = 208f))
        assertEquals(0f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 0f, foldDistance = 208f))
        assertEquals(-30f, AgendaCalendarFold.snapTargetOffset(proposedOffset = -30f, foldDistance = 208f))
        assertEquals(208f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 208f, foldDistance = 208f))
        assertEquals(500f, AgendaCalendarFold.snapTargetOffset(proposedOffset = 500f, foldDistance = 208f))
    }

    @Test
    fun googleMapsUrlSearchesForVenueAndMunicipality() {
        val url = java.net.URI(googleMapsSearchUrl(venue = "Plaça Vella", municipality = "El Vendrell"))

        assertEquals("https", url.scheme)
        assertEquals("www.google.com", url.host)
        assertEquals("/maps/search/", url.path)
        assertEquals("api=1&query=Plaça Vella, El Vendrell", url.query)
    }

    @Test
    fun pagerPagesAreAbsoluteMonthsAndMondayBasedWeeks() {
        val july = AgendaCalendarPaging.monthPage(agendaDate("2026-07-21"))
        assertEquals(july, AgendaCalendarPaging.monthPage(agendaDate("2026-07-01")))
        assertEquals(july + 1, AgendaCalendarPaging.monthPage(agendaDate("2026-08-31")))
        assertEquals("2026-07-01", AgendaCalendarPaging.month(july).toString())
        assertEquals(0, AgendaCalendarPaging.monthPage(agendaDate("1999-12-31")))

        val week = AgendaCalendarPaging.weekPage(agendaDate("2026-07-21"))
        assertEquals(week, AgendaCalendarPaging.weekPage(agendaDate("2026-07-26")))
        assertEquals(week + 1, AgendaCalendarPaging.weekPage(agendaDate("2026-07-27")))
        assertEquals("2026-07-20", AgendaCalendarPaging.week(week).toString())
        assertTrue(AgendaCalendarPaging.week(AgendaCalendarPaging.WEEK_PAGE_COUNT - 1).year == 2099)
    }
}
