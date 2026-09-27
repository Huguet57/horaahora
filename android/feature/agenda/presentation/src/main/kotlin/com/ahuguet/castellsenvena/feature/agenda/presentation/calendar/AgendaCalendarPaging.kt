package com.ahuguet.castellsenvena.feature.agenda.presentation.calendar

import java.time.DayOfWeek
import java.time.LocalDate
import java.time.YearMonth
import java.time.temporal.ChronoUnit
import java.time.temporal.TemporalAdjusters

/**
 * Absolute page numbers for the month and week pagers, counted from January
 * 2000. Fixed pages keep a pager and the model in step without a moving anchor,
 * also after the screen is recreated.
 */
object AgendaCalendarPaging {
    private val firstMonth = YearMonth.of(2000, 1)

    /** 3 January 2000 was a Monday. */
    private val firstMonday = LocalDate.of(2000, 1, 3)

    /** January 2000 to December 2099. */
    const val MONTH_PAGE_COUNT = 1200

    /** The weeks of the same century. */
    const val WEEK_PAGE_COUNT = 5217

    fun monthPage(containing: LocalDate): Int =
        ChronoUnit.MONTHS.between(firstMonth, YearMonth.from(containing)).toInt()
            .coerceIn(0, MONTH_PAGE_COUNT - 1)

    /** The first day of the month shown on [page]. */
    fun month(page: Int): LocalDate = firstMonth.plusMonths(page.toLong()).atDay(1)

    fun weekPage(containing: LocalDate): Int =
        ChronoUnit.WEEKS.between(firstMonday, monday(containing)).toInt()
            .coerceIn(0, WEEK_PAGE_COUNT - 1)

    /** The Monday of the week shown on [page]. */
    fun week(page: Int): LocalDate = firstMonday.plusWeeks(page.toLong())

    internal fun monday(date: LocalDate): LocalDate = date.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))
}
