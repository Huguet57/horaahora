package com.ahuguet.castellsenvena.core.common

import java.time.DayOfWeek
import java.time.LocalDate
import java.time.LocalTime

/**
 * Catalan date labels. They are spelled out here instead of relying on the
 * platform locale data so the app reads the same on every device and in tests.
 */
object CatalanDates {
    private val monthNames = listOf(
        "gener", "febrer", "març", "abril", "maig", "juny",
        "juliol", "agost", "setembre", "octubre", "novembre", "desembre",
    )
    private val weekdayNames = listOf(
        "dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge",
    )

    fun monthName(month: Int): String = monthNames[month - 1]

    fun weekdayName(day: DayOfWeek): String = weekdayNames[day.value - 1]

    /** "de juliol", "d’agost": the month as it appears inside a date. */
    fun monthWithPreposition(month: Int): String {
        val name = monthName(month)
        return if (name.first() in "aeiou") "d’$name" else "de $name"
    }

    /** "juliol del 2026". */
    fun monthAndYear(date: LocalDate): String = "${monthName(date.monthValue)} del ${date.year}"

    /** "dissabte, 25 de juliol del 2026". */
    fun fullDate(date: LocalDate): String =
        "${weekdayName(date.dayOfWeek)}, ${date.dayOfMonth} " +
            "${monthWithPreposition(date.monthValue)} del ${date.year}"

    /** "9:05", "19:04": 24-hour clock without a leading zero. */
    fun time(time: LocalTime): String = "${time.hour}:${time.minute.toString().padStart(2, '0')}"
}

object CatalanNumbers {
    /** Groups thousands with a dot, as Catalan does: 4930 → "4.930". */
    fun grouped(value: Long): String {
        val digits = if (value < 0) (-value).toString() else value.toString()
        val grouped = digits.reversed().chunked(3).joinToString(".").reversed()
        return if (value < 0) "-$grouped" else grouped
    }

    fun grouped(value: Int): String = grouped(value.toLong())
}
