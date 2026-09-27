package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ChatPresentationResponse
import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.domain.chat.PerformanceResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoreRankingRowResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoredCastellResponse
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class PresentationsTest {
    private fun castell(input: String, canonical: String, points: Int, outcome: String = "unloaded", counted: Boolean = true) =
        ScoredCastellResponse(input, canonical, outcome, points, counted, reason = null)

    private fun comparison(
        firstLabel: String = "Vella",
        secondLabel: String = "Joves",
        first: ScoredCastellResponse = castell("4d10fm", "4de10fm", 4930),
        second: ScoredCastellResponse = castell("4d9net", "4de9sf", 4105),
        winnerLabel: String? = firstLabel,
        intent: String = "comparison",
    ) = ChatResponse(
        reply = "Guanya $firstLabel per 825 punts.",
        intent = intent,
        performances = listOf(
            PerformanceResponse(firstLabel, first.points, listOf(first)),
            PerformanceResponse(secondLabel, second.points, listOf(second)),
        ),
        winnerLabel = winnerLabel,
        warnings = emptyList(),
        rulesetVersion = "concurs-2026",
        needsClarification = false,
    )

    private fun ranking(type: String = "score_ranking", focus: String? = null, rows: List<ScoreRankingRowResponse>) =
        ChatResponse(
            reply = "Resposta de compatibilitat.",
            intent = "contest_info",
            performances = emptyList(),
            winnerLabel = null,
            warnings = emptyList(),
            rulesetVersion = "concurs-2026",
            needsClarification = false,
            presentation = ChatPresentationResponse(type, "Rànquing de puntuacions 2026", "both", focus, rows),
        )

    @Test
    fun buildsAComparisonWithCastellsTotalsWinnerAndMargin() {
        val presentation = assertNotNull(ComparisonPresentation.from(comparison()))

        assertEquals(listOf("Vella", "Joves"), presentation.columns.map { it.label })
        assertEquals("4de10fm", presentation.columns[0].castells[0].notation)
        assertEquals("Descarregat", presentation.columns[0].castells[0].result)
        assertEquals(listOf(4_930, 4_105), presentation.columns.map { it.total })
        assertEquals("Vella", presentation.winnerLabel)
        assertEquals(825, presentation.margin)
        assertEquals("Guanya Vella per 825 punts.", presentation.summary)
        assertEquals(1, presentation.maximumCastellCount)
        assertEquals(listOf(true, false), presentation.columns.map { it.isWinner })
    }

    @Test
    fun onlyBuildsForComparisonsWithAtLeastTwoPerformances() {
        assertNull(ComparisonPresentation.from(comparison(intent = "total")))
    }

    @Test
    fun replacesGenericSideNamesWithTheComparedCastells() {
        val presentation = assertNotNull(
            ComparisonPresentation.from(comparison(firstLabel = "costat 1", secondLabel = "costat 2")),
        )

        assertEquals(listOf("Amb 4d10fm", "Amb 4d9net"), presentation.columns.map { it.label })
        assertEquals("Amb 4d10fm", presentation.winnerLabel)
        assertEquals("Guanya Amb 4d10fm per 825 punts.", presentation.summary)
    }

    @Test
    fun usesLettersWhenThereIsNoDistinctiveCastell() {
        val tied = castell("5d9f", "5de9f", 3125)
        val presentation = assertNotNull(
            ComparisonPresentation.from(
                comparison(firstLabel = "costat 1", secondLabel = "costat 2", first = tied, second = tied, winnerLabel = null),
            ),
        )

        assertEquals(listOf("A", "B"), presentation.columns.map { it.label })
        assertNull(presentation.winnerLabel)
        assertEquals("Empat a 3.125 punts.", presentation.summary)
    }

    @Test
    fun buildsRowsAndTotalForASingleCalculatedPerformance() {
        val response = ChatResponse(
            reply = "Total: 20.615 punts.",
            intent = "total",
            performances = listOf(
                PerformanceResponse(
                    label = "Actuació",
                    total = 20_615,
                    castells = listOf(castell("3d10sm", "3de10sm", 7_475), castell("2d10fmp", "2de10fmp", 6_780)),
                ),
            ),
            winnerLabel = null,
            warnings = emptyList(),
            rulesetVersion = "concurs-2026",
            needsClarification = false,
        )

        val presentation = assertNotNull(PerformanceSummaryPresentation.from(response))

        assertEquals("Actuació calculada", presentation.title)
        assertEquals(listOf("3de10sm", "2de10fmp"), presentation.rows.map { it.notation })
        assertEquals("Descarregat", presentation.rows.first().result)
        assertEquals(20_615, presentation.total)
    }

    @Test
    fun performanceSummaryDoesNotReplaceComparisons() {
        val response = comparison().copy(performances = emptyList())

        assertNull(PerformanceSummaryPresentation.from(response))
    }

    @Test
    fun buildsRankingRowsFromStructuredResponse() {
        val presentation = assertNotNull(
            ScorePresentation.from(
                ranking(
                    rows = listOf(
                        ScoreRankingRowResponse(1, "3de10sm", 6205, 7475),
                        ScoreRankingRowResponse(2, "4de10sm", 5910, 7120),
                    ),
                ),
            ),
        )

        assertEquals("Rànquing de puntuacions 2026", presentation.title)
        assertEquals(ScorePresentation.Outcome.BOTH, presentation.outcome)
        assertNull(presentation.focusNotation)
        assertEquals(listOf("3de10sm", "4de10sm"), presentation.rows.map { it.notation })
        assertEquals(listOf(7_475, 7_120), presentation.rows.map { it.unloadedPoints })
    }

    @Test
    fun buildsFocusedRankingWithNeighbors() {
        val presentation = assertNotNull(
            ScorePresentation.from(
                ranking(
                    focus = "Pde7sf",
                    rows = listOf(
                        ScoreRankingRowResponse(3, "2de10fmp", 5630, 6780),
                        ScoreRankingRowResponse(4, "Pde7sf", 5280, 6360),
                        ScoreRankingRowResponse(5, "3de9sf", 5165, 6220),
                    ),
                ),
            ),
        )

        assertEquals("Pde7sf", presentation.focusNotation)
        assertEquals(listOf(3, 4, 5), presentation.rows.map { it.position })
    }

    @Test
    fun rejectsLegacyScoreCards() {
        assertNull(ScorePresentation.from(ranking(type = "score_card", rows = emptyList())))
    }

    @Test
    fun structuredPresentationsTakePrecedenceOverTheProse() {
        assertIs<CalculationPresentation.Comparison>(CalculationPresentation.from(comparison()))
        assertIs<CalculationPresentation.Ranking>(CalculationPresentation.from(ranking(rows = emptyList())))
        assertNull(CalculationPresentation.from(comparison(intent = "clarification")))
        assertNull(CalculationPresentation.from(null))
    }

    @Test
    fun outcomesUseCatalanLabels() {
        assertEquals("Carregat", castellResultLabel("loaded"))
        assertEquals("Descarregat", castellResultLabel("unloaded"))
        assertEquals("Intent", castellResultLabel("attempt"))
        assertEquals("Desmuntat", castellResultLabel("desmuntat"))
    }

    @Test
    fun conversationAgeUsesMinutesAsTheSmallestUnitAndAtMostTwoUnits() {
        val now = Instant.ofEpochSecond(1_000_000)
        fun age(secondsAgo: Long) = ConversationAgeFormatter.format(now.minusSeconds(secondsAgo), now)

        assertEquals("menys d’1 min", age(5))
        assertEquals("29 min", age(29 * 60 + 21))
        assertEquals("34 min", age(34 * 60 + 6))
        assertEquals("1 h", age(60 * 60))
        assertEquals("1 h i 1 min", age(60 * 60 + 60))
        assertEquals("2 dies i 9 h", age(2 * 24 * 60 * 60 + 9 * 60 * 60))
        assertEquals("1 dia", age(24 * 60 * 60))
        assertEquals("menys d’1 min", age(-30))
    }
}
