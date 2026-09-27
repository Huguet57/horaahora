package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourItemMerger.Policy
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class HourByHourItemMergerTest {
    @Test
    fun revalidationUpdatesKnownItemsAndPreservesPaginatedItems() {
        val existing = listOf(item("first", title = "Original"), item("paginated"))

        val result = HourByHourItemMerger.merge(listOf(item("first", title = "Actualitzat")), existing, Policy.REVALIDATE)

        assertEquals(listOf("first", "paginated"), result.items.map { it.id })
        assertEquals("Actualitzat", result.items.first().title)
        assertFalse(result.containsNewItems)
    }

    @Test
    fun revalidationSignalsAnIdentityThatWasNotPreviouslyLoaded() {
        val result = HourByHourItemMerger.merge(listOf(item("second"), item("first")), listOf(item("first")), Policy.REVALIDATE)

        assertEquals(listOf("second", "first"), result.items.map { it.id })
        assertTrue(result.containsNewItems)
    }

    @Test
    fun paginationAppendsWithoutSignallingNewContent() {
        val result = HourByHourItemMerger.merge(listOf(item("older")), listOf(item("first")), Policy.APPEND)

        assertEquals(listOf("first", "older"), result.items.map { it.id })
        assertFalse(result.containsNewItems)
    }

    @Test
    fun identityComponentsCannotCollideThroughTheirSeparator() {
        val existing = listOf(item("existing", sourceId = "source:part", externalId = "entry"))
        val incoming = listOf(item("incoming", sourceId = "source", externalId = "part:entry"))

        val result = HourByHourItemMerger.merge(incoming, existing, Policy.REVALIDATE)

        assertEquals(listOf("incoming", "existing"), result.items.map { it.id })
        assertTrue(result.containsNewItems)
    }
}
