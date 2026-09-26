package com.ahuguet.castellsenvena.core.common

import java.time.LocalDate
import java.time.LocalTime
import kotlin.test.Test
import kotlin.test.assertEquals

class CatalanFormatTest {
    @Test
    fun monthTitleAndFullDateKeepTheIOSCopy() {
        val july = LocalDate.of(2026, 7, 25)

        assertEquals("juliol del 2026", CatalanDates.monthAndYear(july))
        assertEquals("dissabte, 25 de juliol del 2026", CatalanDates.fullDate(july))
    }

    @Test
    fun monthsStartingWithAVowelUseTheElidedPreposition() {
        assertEquals("dijous, 6 d’agost del 2026", CatalanDates.fullDate(LocalDate.of(2026, 8, 6)))
        assertEquals("d’abril", CatalanDates.monthWithPreposition(4))
        assertEquals("d’octubre", CatalanDates.monthWithPreposition(10))
        assertEquals("de setembre", CatalanDates.monthWithPreposition(9))
    }

    @Test
    fun timeUsesTheTwentyFourHourClockWithoutLeadingZero() {
        assertEquals("0:06", CatalanDates.time(LocalTime.of(0, 6)))
        assertEquals("19:04", CatalanDates.time(LocalTime.of(19, 4)))
    }

    @Test
    fun numbersGroupThousandsWithADot() {
        assertEquals("825", CatalanNumbers.grouped(825))
        assertEquals("4.930", CatalanNumbers.grouped(4_930))
        assertEquals("20.615", CatalanNumbers.grouped(20_615))
        assertEquals("1.234.567", CatalanNumbers.grouped(1_234_567))
        assertEquals("-1.200", CatalanNumbers.grouped(-1_200))
        assertEquals("0", CatalanNumbers.grouped(0))
    }
}
