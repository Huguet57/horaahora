package com.ahuguet.castellsenvena.feature.scoretable.presentation

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ScoreTableTest {
    private val table = ScoreTable.bundled()

    @Test
    fun theBundledTableHasEveryCastell() {
        assertEquals(47, table.castells.size)
        assertEquals(ScoreTableCastell("2de6", "Torre de sis", group = 1, loaded = 250, unloaded = 300), table.castells.first())
    }

    @Test
    fun castellsGoFromTheMostPointsToTheFewest() {
        val castells = table.sectionsByPoints.flatMap { it.castells }

        assertEquals(47, castells.size)
        assertEquals("3de10sm", castells.first().notation)
        assertEquals("2de6", castells.last().notation)
        castells.zipWithNext().forEach { (castell, next) ->
            assertTrue(castell.unloaded >= next.unloaded, castell.notation)
        }
    }

    @Test
    fun eachGroupIsOneSectionFromTheHighest() {
        val sections = table.sectionsByPoints

        assertEquals(listOf(7, 6, 5, 4, 3, 2, 1), sections.map { it.group })
        assertEquals(listOf("3de10sm", "4de10sm", "2de10fmp"), sections.first().castells.take(3).map { it.notation })
        assertEquals(sections.size, sections.map { it.key }.toSet().size)
    }

    @Test
    fun aTappedCastellHighlightsTheCastellsBelowWhoseDescarregatBeatsItsCarregat() {
        // 3.285 and 3.125 descarregat beat 3.100 carregat.
        assertEquals(listOf("4de9fa", "5de9f"), table.notationsBelowWhoseUnloadedBeats(loadedOf = castell("3de9fa")))
    }

    @Test
    fun castellsAboveAreLeftOutBecauseTheyObviouslyWin() {
        assertEquals(
            listOf("Pde9fmp", "2de9sm", "9de9f"),
            table.notationsBelowWhoseUnloadedBeats(loadedOf = castell("3de9sf")),
        )
    }

    @Test
    fun aLowerCastellCanBeatTheCarregatOfAHigherOne() {
        assertEquals(
            listOf("2de9fm", "3de8s", "9de8"),
            table.notationsBelowWhoseUnloadedBeats(loadedOf = castell("Pde8fm")),
        )
    }

    @Test
    fun aTieDoesNotWin() {
        // 5de7a's 670 descarregat only ties 670 carregat.
        assertEquals(listOf("9de7", "3de7s"), table.notationsBelowWhoseUnloadedBeats(loadedOf = castell("2de7")))
    }

    private fun castell(notation: String) = table.castells.first { it.notation == notation }
}
