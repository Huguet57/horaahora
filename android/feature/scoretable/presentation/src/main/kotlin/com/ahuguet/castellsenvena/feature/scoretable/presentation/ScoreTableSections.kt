package com.ahuguet.castellsenvena.feature.scoretable.presentation

/** A run of castells of the same group. */
data class ScoreTableSection(val group: Int, val castells: List<ScoreTableCastell>) {
    val key: String get() = castells.firstOrNull()?.notation ?: "grup-$group"
}

private val byPoints = compareByDescending<ScoreTableCastell> { it.unloaded }.thenByDescending { it.loaded }

/**
 * From the castell worth the most to the one worth the least, descarregat first
 * and then carregat, with a new section wherever the group changes.
 */
val ScoreTable.sectionsByPoints: List<ScoreTableSection>
    get() {
        val sections = mutableListOf<ScoreTableSection>()
        for (castell in castells.sortedWith(byPoints)) {
            val last = sections.lastOrNull()
            if (last != null && last.group == castell.group) {
                sections[sections.lastIndex] = last.copy(castells = last.castells + castell)
            } else {
                sections += ScoreTableSection(castell.group, listOf(castell))
            }
        }
        return sections
    }

/**
 * The castells below [loadedOf] in the table whose descarregat is worth more than
 * its carregat: what beats loading it. Castells above obviously do, and a tie
 * does not win.
 */
fun ScoreTable.notationsBelowWhoseUnloadedBeats(loadedOf: ScoreTableCastell): List<String> =
    sectionsByPoints
        .flatMap { it.castells }
        .filter { byPoints.compare(it, loadedOf) > 0 && it.unloaded > loadedOf.loaded }
        .map { it.notation }
