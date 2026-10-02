package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ScoredCastellResponse

/**
 * One line under a calculation table saying which castells do not count and why.
 * Attempts are left out: their cell already reads «Intent».
 */
object NotCountedNote {
    fun text(performances: List<Pair<String, List<ScoredCastellResponse>>>): String? {
        val parts = performances.mapNotNull { (label, castells) ->
            reasons(castells)?.let { (text, count) -> Triple(label, text, count) }
        }
        if (parts.isEmpty()) return null
        val lead = if (parts.sumOf { it.third } == 1) "No compta" else "No compten"
        if (performances.size == 1) return "$lead: ${parts.single().second}."
        return "$lead — " + parts.joinToString(" ") { (label, text) -> "$label: $text." }
    }

    private fun reasons(castells: List<ScoredCastellResponse>): Pair<String, Int>? {
        val notations = linkedMapOf<String, MutableList<String>>()
        for (castell in castells) {
            if (castell.counted) continue
            val reason = castell.reason?.let(::label) ?: continue
            notations.getOrPut(reason) { mutableListOf() } += castell.canonical ?: castell.input
        }
        if (notations.isEmpty()) return null
        val text = notations.entries.joinToString(", ") { (reason, items) -> "${joined(items)} ($reason)" }
        return text to notations.values.sumOf { it.size }
    }

    private fun label(reason: String): String? = when (reason) {
        "duplicate_structure" -> "repetit"
        "loaded_limit" -> "només compten 2 carregats"
        "outside_top_three" -> "fora de les 3 millors"
        else -> null
    }

    private fun joined(items: List<String>): String =
        if (items.size <= 1) items.joinToString() else items.dropLast(1).joinToString(", ") + " i " + items.last()
}
