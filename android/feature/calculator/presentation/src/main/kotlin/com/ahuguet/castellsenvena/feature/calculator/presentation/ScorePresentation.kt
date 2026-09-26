package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse

/** A slice of the 2026 score table, optionally centred on one castell. */
data class ScorePresentation(
    val title: String,
    val outcome: Outcome,
    val focusNotation: String?,
    val rows: List<Row>,
) {
    enum class Outcome {
        LOADED,
        UNLOADED,
        BOTH,
    }

    data class Row(
        val position: Int,
        val notation: String,
        val loadedPoints: Int,
        val unloadedPoints: Int,
    )

    companion object {
        fun from(response: ChatResponse): ScorePresentation? {
            val source = response.presentation ?: return null
            if (source.type != "score_ranking") return null
            val outcome = when (source.outcome) {
                "loaded" -> Outcome.LOADED
                "unloaded" -> Outcome.UNLOADED
                "both" -> Outcome.BOTH
                else -> return null
            }
            return ScorePresentation(
                title = source.title,
                outcome = outcome,
                focusNotation = source.focusNotation,
                rows = source.rows.map { Row(it.position, it.notation, it.loadedPoints, it.unloadedPoints) },
            )
        }
    }
}

/** The castells of a single performance, for a score lookup or a total. */
data class PerformanceSummaryPresentation(
    val title: String,
    val rows: List<Row>,
    val total: Int,
) {
    data class Row(
        val notation: String,
        val result: String,
        val points: Int,
        val counted: Boolean,
    )

    companion object {
        fun from(response: ChatResponse): PerformanceSummaryPresentation? {
            if (response.intent !in setOf("lookup", "total") ||
                response.performances.size != 1 ||
                response.needsClarification
            ) {
                return null
            }
            val performance = response.performances.single()
            return PerformanceSummaryPresentation(
                title = if (response.intent == "lookup") "Puntuació" else "Actuació calculada",
                rows = performance.castells.map { castell ->
                    Row(
                        notation = castell.canonical ?: castell.input,
                        result = castellResultLabel(castell.outcome),
                        points = castell.points,
                        counted = castell.counted,
                    )
                },
                total = performance.total,
            )
        }
    }
}
