package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import kotlin.test.Test
import kotlin.test.assertEquals

class ComparatorScenarioSummaryTest {
    private val rules = ComparatorRules(ScoreTable.bundled())

    @Test
    fun theTitleIsWhoWinsAndByHowMuchAndEachLineListsAColla() {
        val scenario = ComparatorScenario(
            colles = listOf(
                colla(d("3de10fm"), d("4de10fm"), c("9de9f"), shortName = "VIL"),
                colla(d("4de9sf"), d("4de10fm"), c("3de9sf"), shortName = "VELLA"),
            ),
        )

        val summary = rules.summary(scenario)

        assertEquals("VELLA +450", summary.title)
        assertEquals(listOf("VIL 3d10fm 4d10fm 9d9fc", "VELLA 4d9sf 4d10fm 3d9sfc"), summary.lines)
    }

    @Test
    fun attemptsReadAsInCastellerNotationAndCollesWithoutCastellsAreLeftOut() {
        val scenario = ComparatorScenario(
            colles = listOf(
                colla(i("3de10fm"), null, id("Pde8fm"), shortName = "VIL"),
                colla(shortName = "VELLA"),
            ),
        )

        assertEquals(listOf("VIL 3d10fmi Pd8fmid"), rules.summary(scenario).lines)
    }

    @Test
    fun aTieAndAnEmptyScenarioSaySo() {
        val tie = ComparatorScenario(colles = listOf(colla(d("3de9f"), shortName = "VIL"), colla(d("3de9f"), shortName = "VELLA")))
        val empty = ComparatorScenario(colles = listOf(colla(shortName = "VIL"), colla(shortName = "VELLA")))

        assertEquals("Empat", rules.summary(tie).title)
        assertEquals("Sense castells", rules.summary(empty).title)
    }
}
