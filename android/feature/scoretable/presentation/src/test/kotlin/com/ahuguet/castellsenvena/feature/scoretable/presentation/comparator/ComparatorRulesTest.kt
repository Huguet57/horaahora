package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ComparatorRulesTest {
    private val rules = ComparatorRules(ScoreTable.bundled())

    // Scoring

    @Test
    fun theThreeBestConstructionsCount() {
        val score = rules.score(colla(d("3de10fm"), d("4de10fm"), c("2de9sm"), d("3de9f")))

        assertEquals(4_525 + 4_930 + 4_685, score.total)
        assertEquals(notCounted(NotCountedReason.OUTSIDE_TOP_THREE), score.rounds[3].status)
    }

    @Test
    fun atMostTwoLoadedCastellsCount() {
        val score = rules.score(colla(c("3de10fm"), c("4de10fm"), c("2de9sm"), d("3de9f")))

        assertEquals(4_095 + 4_685 + 1_910, score.total)
        assertEquals(notCounted(NotCountedReason.LOADED_LIMIT), score.rounds[0].status)
        assertEquals(RoundScore.Status.Counted, score.rounds[3].status)
    }

    @Test
    fun attemptsTakeARoundButScoreNothing() {
        val score = rules.score(colla(i("3de10fm"), d("4de9f")))

        assertEquals(1_820, score.total)
        assertEquals(0, score.rounds[0].points)
        assertEquals(notCounted(NotCountedReason.ATTEMPT), score.rounds[0].status)
    }

    @Test
    fun aCastellAchievedTwiceCountsOnlyOnce() {
        val score = rules.score(colla(c("3de9f"), d("3de9f"), d("4de8")))

        assertEquals(1_910 + 845, score.total)
        assertEquals(notCounted(NotCountedReason.REPEATED), score.rounds[0].status)
        // Using two rounds for the same castell is a double penalty.
        assertEquals(2, score.penalties)
    }

    @Test
    fun anEmptyPerformanceScoresZero() {
        val score = rules.score(ComparatorColla(name = "Buida", shortName = "B"))

        assertEquals(0, score.total)
        assertTrue(score.rounds.all { it.status == RoundScore.Status.Empty })
    }

    // Ranking

    @Test
    fun theRankingGoesByPointsAndThenByPenalties() {
        val first = colla(d("3de9f"), penalties = 1)
        val second = colla(d("3de9f"), penalties = 0)
        val third = colla(d("4de9f"))

        val ranking = rules.ranking(listOf(first, second, third))

        assertEquals(listOf(second.id, first.id, third.id), ranking.map { it.collaId })
        assertEquals(ComparatorStanding.TieBreak.PENALTIES, ranking[0].tieBreak)
    }

    @Test
    fun aTieWithTheSamePenaltiesGoesToTheBestCastell() {
        val lowerBest = colla(d("2de6"), c("9de6")) // 300 + 295 = 595
        val higherBest = colla(c("2de6"), c("3de7")) // 250 + 345 = 595

        val ranking = rules.ranking(listOf(lowerBest, higherBest))

        assertEquals(listOf(higherBest.id, lowerBest.id), ranking.map { it.collaId })
        assertEquals(ComparatorStanding.TieBreak.BEST_CASTELL, ranking[0].tieBreak)
        assertNull(rules.ranking(listOf(higherBest, colla(d("3de9f"))))[0].tieBreak)
    }

    // Allowed attempts

    @Test
    fun aCastellAlreadyUnloadedCannotBeTriedAgain() {
        assertEquals(ComparatorRestriction.AlreadyUnloaded, rules.restriction("3de9f", 1, colla(d("3de9f"))))
    }

    @Test
    fun aCastellTriedTwiceCannotBeTriedAgain() {
        assertEquals(ComparatorRestriction.TriedTwice, rules.restriction("3de10fm", 2, colla(i("3de10fm"), i("3de10fm"))))
    }

    @Test
    fun aLoadedCastellCanBeTriedAgain() {
        assertNull(rules.restriction("3de9f", 1, colla(c("3de9f"))))
    }

    @Test
    fun anotherHeightOfTheSameBaseAsACountedCastellIsNotAllowed() {
        val plan = colla(d("3de9f"))

        assertEquals(ComparatorRestriction.SameBase("3de9f"), rules.restriction("3de10fm", 1, plan))
        // The versions without folre are a different base.
        assertNull(rules.restriction("3de9sf", 1, plan))
    }

    @Test
    fun onlyEarlierRoundsRestrictALaterOne() {
        assertNull(rules.restriction("3de9f", 0, colla(null, null, d("3de9f"))))
    }

    @Test
    fun theLastTwoRoundsNeedAnImprovementOnceThreeCastellsAreDone() {
        val plan = colla(d("3de9f"), d("4de9f"), d("2de8f"))

        assertEquals(ComparatorRestriction.NoImprovement, rules.restriction("5de7", 3, plan))
        assertNull(rules.restriction("3de8s", 3, plan))
        // With fewer than three castells done, any castell of the table is allowed.
        assertNull(rules.restriction("4de8", 3, colla(d("3de9f"), i("4de9f"), d("2de8f"))))
    }

    @Test
    fun theLastTwoRoundsAllowRepeatingALoadedCastell() {
        assertNull(rules.restriction("2de8f", 3, colla(d("3de9f"), d("4de9f"), c("2de8f"))))
    }

    // Steps

    @Test
    fun stepsMoveToTheNeighbourInPointsAndSkipWhatIsNotAllowed() {
        val plan = colla(d("3de10fm"), d("9de9f"), d("4de9sf"))

        // Above 4de9sf (4.105) come 2de8sf (4.310) and then 3de10fm (4.525), already unloaded.
        assertEquals("2de8sf", rules.step(d("4de9sf"), 2, plan, direction = 1)?.notation)
        assertEquals("4de10fm", rules.step(d("2de8sf"), 2, plan, direction = 1)?.notation)
        assertEquals("3de9fa", rules.step(d("4de9sf"), 2, plan, direction = -1)?.notation)
    }

    @Test
    fun stepsFollowTheCarregatPointsForALoadedCastell() {
        val plan = colla()

        // Carregat: 3de9f 1.585, 5de8a 1.555, 4de9f 1.510.
        assertEquals("3de9f", rules.step(c("5de8a"), 0, plan, direction = 1)?.notation)
        assertEquals("4de9f", rules.step(c("5de8a"), 0, plan, direction = -1)?.notation)
    }

    @Test
    fun theTopOfTheTableHasNoStepUp() {
        assertNull(rules.step(d("3de10sm"), 0, colla(), direction = 1))
    }

    // Points

    @Test
    fun pointsAndMarginsReadAsTheConcursWritesThem() {
        assertEquals("4.525", formattedPoints(4_525))
        assertEquals("−600", formattedPoints(-600))
        assertEquals("+1.200", formattedMargin(1_200))
        assertEquals("=", formattedMargin(0))
    }
}

internal fun colla(vararg rounds: PlannedCastell?, penalties: Int = 0, shortName: String = "PRV"): ComparatorColla {
    val all = List(ComparatorColla.ROUND_COUNT) { rounds.getOrNull(it) }
    return ComparatorColla(name = shortName, shortName = shortName, rounds = all, penalties = penalties)
}

internal fun d(notation: String) = PlannedCastell(notation, ComparatorOutcome.UNLOADED)

internal fun c(notation: String) = PlannedCastell(notation, ComparatorOutcome.LOADED)

internal fun i(notation: String) = PlannedCastell(notation, ComparatorOutcome.ATTEMPT)

internal fun id(notation: String) = PlannedCastell(notation, ComparatorOutcome.DISMANTLED_ATTEMPT)

private fun notCounted(reason: NotCountedReason) = RoundScore.Status.NotCounted(reason)
