package com.ahuguet.castellsenvena.core.common

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class TextFoldingTest {
    @Test
    fun foldingIgnoresCaseAccentsAndWidth() {
        assertEquals("castellers de la vila de gracia", TextFolding.fold("CASTELLERS DE LA VILA DE GRÀCIA"))
        assertEquals("abc", TextFolding.fold("ＡＢＣ"))
    }

    @Test
    fun wordsSplitOnAnyWhitespaceIncludingNonBreakingSpaces() {
        assertEquals(listOf("Colla", "Vella"), TextFolding.words("  Colla \tVella \n"))
    }

    @Test
    fun searchMatchesIgnoringCaseAndAccents() {
        assertTrue(TextFolding.containsIgnoringCaseAndAccents("Castellers de la Vila de Gràcia", "gracia"))
        assertTrue(TextFolding.containsIgnoringCaseAndAccents("Minyons de Terrassa", "MINY"))
        assertFalse(TextFolding.containsIgnoringCaseAndAccents("Minyons de Terrassa", "Valls"))
    }

    @Test
    fun urlComponentsKeepOnlyUnreservedCharacters() {
        assertEquals("Pla%C3%A7a%20Vella%2C%20El%20Vendrell", UrlEncoding.encodeComponent("Plaça Vella, El Vendrell"))
        assertEquals("a%0Ab", UrlEncoding.encodeComponent("a\nb"))
        assertEquals("safe-._~", UrlEncoding.encodeComponent("safe-._~"))
    }
}
