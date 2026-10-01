package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoredCastellResponse

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

/**
 * Why an uncounted castell is left out, with the comparator's wording; null when it counts.
 * An attempt already reads «Intent», so it needs no extra label.
 */
fun notCountedReasonLabel(castell: ScoredCastellResponse): String? {
    if (castell.counted) return null
    return when (castell.reason) {
        "duplicate_structure" -> "repetit"
        "loaded_limit" -> "3r carregat"
        "outside_top_three" -> "fora de les 3"
        else -> null
    }
}

object CalculatorPrompts {
    val suggestions = listOf(
        "Què guanya, el 5d9f o el 4d9fa?",
        "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?",
        "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
    )
}
