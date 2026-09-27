package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.core.common.TextFolding
import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.domain.chat.PerformanceResponse

/** Two or more performances side by side, with totals, winner and margin. */
data class ComparisonPresentation(
    val columns: List<Column>,
    val winnerLabel: String?,
    val margin: Int?,
    val summary: String,
    val maximumCastellCount: Int,
) {
    data class Castell(
        val notation: String,
        val result: String,
        val points: Int,
        val counted: Boolean,
    )

    data class Column(
        val label: String,
        val total: Int,
        val castells: List<Castell>,
        val isWinner: Boolean,
    )

    companion object {
        private val genericRoots = setOf("costat", "opció", "opcio", "actuació", "actuacio")
        private const val ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        fun from(response: ChatResponse): ComparisonPresentation? {
            if (response.intent != "comparison" ||
                response.performances.size < 2 ||
                response.needsClarification
            ) {
                return null
            }

            val displayLabels = displayLabels(response.performances)
            val columns = response.performances.mapIndexed { index, performance ->
                Column(
                    label = displayLabels[index],
                    total = performance.total,
                    castells = performance.castells.map { castell ->
                        Castell(
                            notation = castell.canonical ?: castell.input,
                            result = castellResultLabel(castell.outcome),
                            points = castell.points,
                            counted = castell.counted,
                        )
                    },
                    isWinner = performance.label == response.winnerLabel,
                )
            }

            val winnerIndex = response.winnerLabel?.let { winner ->
                response.performances.indexOfFirst { it.label == winner }.takeIf { it >= 0 }
            }
            val winnerLabel = winnerIndex?.let(displayLabels::get)
            val margin: Int?
            val summary: String
            if (winnerLabel != null) {
                val totals = response.performances.map { it.total }.sortedDescending()
                margin = totals[0] - totals[1]
                summary = "Guanya $winnerLabel per ${CatalanNumbers.grouped(margin)} punts."
            } else {
                margin = null
                summary = "Empat a ${CatalanNumbers.grouped(response.performances.first().total)} punts."
            }

            return ComparisonPresentation(
                columns = columns,
                winnerLabel = winnerLabel,
                margin = margin,
                summary = summary,
                maximumCastellCount = columns.maxOf { it.castells.size },
            )
        }

        /**
         * Generic side names ("costat 1", "A", or the castell itself) are replaced
         * by the castell that tells the performances apart, or by letters.
         */
        private fun displayLabels(performances: List<PerformanceResponse>): List<String> {
            val notationSets = performances.map { performance ->
                performance.castells.mapTo(HashSet()) { compact(it.input) }
            }
            val generic = performances.map { isGenericLabel(it.label, it) }
            val used = performances.indices
                .filterNot { generic[it] }
                .mapTo(HashSet()) { compact(performances[it].label) }

            val labels = performances.mapIndexed { index, performance ->
                if (!generic[index]) return@mapIndexed performance.label.trim()
                val otherNotations = notationSets.filterIndexed { other, _ -> other != index }.flatten().toSet()
                val distinctive = performance.castells
                    .firstOrNull { compact(it.input) !in otherNotations }
                    ?.input
                    ?.trim()
                val proposed = distinctive?.let { "Amb $it" }
                if (proposed != null && compact(proposed) !in used) {
                    used += compact(proposed)
                    proposed
                } else {
                    null
                }
            }.toMutableList()

            for (index in labels.indices) {
                if (labels[index] != null) continue
                var candidateIndex = index
                var fallback: String
                do {
                    fallback = if (candidateIndex < ALPHABET.length) {
                        ALPHABET[candidateIndex].toString()
                    } else {
                        "A${candidateIndex + 1}"
                    }
                    candidateIndex += 1
                } while (compact(fallback) in used)
                labels[index] = fallback
                used += compact(fallback)
            }
            return labels.map { it!! }
        }

        private fun isGenericLabel(label: String, performance: PerformanceResponse): Boolean {
            val normalized = compact(label)
            if (normalized.length == 1 && normalized.first().isLetter()) return true
            val parts = normalized.split(' ')
            if (parts.size == 2 &&
                parts[0] in genericRoots &&
                (parts[1].toIntOrNull() != null || (parts[1].length == 1 && parts[1].first().isLetter()))
            ) {
                return true
            }
            val withoutSpaces = normalized.replace(" ", "")
            return performance.castells.any { castell ->
                compact(castell.input).replace(" ", "") == withoutSpaces ||
                    compact(castell.canonical ?: "").replace(" ", "") == withoutSpaces
            }
        }

        private fun compact(value: String): String = TextFolding.words(value.lowercase()).joinToString(" ")
    }
}
