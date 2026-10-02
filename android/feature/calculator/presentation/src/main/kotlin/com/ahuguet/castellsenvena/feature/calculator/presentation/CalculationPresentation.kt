package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse

/**
 * How an assistant answer is drawn. The prose reply is the fallback when none
 * of the structured presentations applies.
 */
sealed interface CalculationPresentation {
    data class Comparison(val presentation: ComparisonPresentation) : CalculationPresentation

    data class Ranking(val presentation: ScorePresentation) : CalculationPresentation

    data class Summary(val presentation: PerformanceSummaryPresentation) : CalculationPresentation

    companion object {
        fun from(response: ChatResponse?): CalculationPresentation? {
            if (response == null) return null
            ComparisonPresentation.from(response)?.let { return Comparison(it) }
            ScorePresentation.from(response)?.let { return Ranking(it) }
            PerformanceSummaryPresentation.from(response)?.let { return Summary(it) }
            return null
        }
    }
}

/** Catalan label of a castell outcome. */
fun castellResultLabel(outcome: String): String = when (outcome) {
    "loaded" -> "Carregat"
    "unloaded" -> "Descarregat"
    "attempt" -> "Intent"
    else -> outcome.split(' ').joinToString(" ") { word ->
        word.lowercase().replaceFirstChar(Char::titlecase)
    }
}

object CalculatorPrompts {
    val suggestions = listOf(
        "Què guanya, el 5d9f o el 4d9fa?",
        "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?",
        "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
    )
}
