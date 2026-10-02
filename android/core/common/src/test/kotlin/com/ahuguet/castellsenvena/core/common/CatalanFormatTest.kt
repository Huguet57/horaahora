package com.ahuguet.castellsenvena.core.common

import kotlin.test.Test
import kotlin.test.assertEquals

class CatalanFormatTest {
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
