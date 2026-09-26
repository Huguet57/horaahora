package com.ahuguet.castellsenvena.feature.agenda.presentation.calendar

import com.ahuguet.castellsenvena.core.common.CatalanDates
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.YearMonth
import java.time.ZoneId
import java.time.temporal.TemporalAdjusters
import java.util.concurrent.ConcurrentHashMap

/** An inclusive range of calendar days. */
data class DateRange(val start: LocalDate, val end: LocalDate)

/**
 * Date math for the agenda: Monday-based weeks in the Europe/Madrid calendar,
 * month grids and prefetch windows.
 */
object AgendaCalendarMath {
    val zone: ZoneId = ZoneId.of("Europe/Madrid")

    /** Month grids are immutable; a small cache avoids rebuilding them while the calendar folds. */
    private val monthRowsCache = ConcurrentHashMap<YearMonth, List<List<LocalDate>>>()
    private const val MONTH_ROWS_CACHE_SIZE = 36

    fun today(): LocalDate = LocalDate.now(zone)

    fun week(containing: LocalDate): List<LocalDate> {
        val monday = containing.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))
        return (0L until 7L).map(monday::plusDays)
    }

    /**
     * Full Monday-based weeks covering the month that contains [containing].
     * Every row has 7 days, including adjacent-month days at both ends.
     */
    fun monthWeekRows(containing: LocalDate): List<List<LocalDate>> {
        val month = YearMonth.from(containing)
        monthRowsCache[month]?.let { return it }

        val lastDay = month.atEndOfMonth()
        var rowStart = week(month.atDay(1)).first()
        val rows = mutableListOf<List<LocalDate>>()
        while (!rowStart.isAfter(lastDay)) {
            rows += (0L until 7L).map(rowStart::plusDays)
            rowStart = rowStart.plusDays(7)
        }
        if (monthRowsCache.size >= MONTH_ROWS_CACHE_SIZE) monthRowsCache.clear()
        monthRowsCache[month] = rows
        return rows
    }

    /** The number of grid rows, without building the grid. */
    fun monthWeekRowCount(containing: LocalDate): Int {
        val month = YearMonth.from(containing)
        val leadingDays = month.atDay(1).dayOfWeek.value - DayOfWeek.MONDAY.value
        return (leadingDays + month.lengthOfMonth() + 6) / 7
    }

    /** The row that contains [date], or null when the day is outside the grid. */
    fun weekRowIndex(of: LocalDate, rows: List<List<LocalDate>>): Int? =
        rows.indexOfFirst { of in it }.takeIf { it >= 0 }

    /**
     * Six months before and after the month that contains [containing], as two
     * ranges: up to the end of that month, and the following months.
     */
    fun prefetchRanges(containing: LocalDate): List<DateRange> {
        val monthStart = containing.withDayOfMonth(1)
        return listOf(
            DateRange(monthStart.minusMonths(6), monthStart.plusMonths(1).minusDays(1)),
            DateRange(monthStart.plusMonths(1), monthStart.plusMonths(7).minusDays(1)),
        )
    }

    fun monthRange(containing: LocalDate): DateRange {
        val month = YearMonth.from(containing)
        return DateRange(month.atDay(1), month.atEndOfMonth())
    }

    /** `yyyy-MM-dd`, the format of [com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent.localDate]. */
    fun localDateKey(date: LocalDate): String = date.toString()

    /** `yyyy-MM`. */
    fun monthKey(date: LocalDate): String = YearMonth.from(date).toString()

    fun monthStarts(from: LocalDate, through: LocalDate): List<LocalDate> {
        val result = mutableListOf<LocalDate>()
        var month = from.withDayOfMonth(1)
        while (!month.isAfter(through)) {
            result += month
            month = month.plusMonths(1)
        }
        return result
    }

    /** "juliol del 2026". */
    fun monthTitle(date: LocalDate): String = CatalanDates.monthAndYear(date)

    /** "dissabte, 25 de juliol del 2026". */
    fun accessibilityDate(date: LocalDate): String = CatalanDates.fullDate(date)
}
