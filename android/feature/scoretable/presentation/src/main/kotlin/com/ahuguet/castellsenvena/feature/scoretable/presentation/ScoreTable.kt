package com.ahuguet.castellsenvena.feature.scoretable.presentation

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** A castell of the official score table and its points. */
@Serializable
data class ScoreTableCastell(
    val notation: String,
    /** The notation read out in Catalan, for screen readers. */
    val name: String,
    val group: Int,
    val loaded: Int,
    val unloaded: Int,
)

/**
 * The official table of the Concurs de Castells 2026 that the app bundles.
 *
 * `scripts/export_score_table.py` generates it from the backend CSV, which stays
 * the only source of the points.
 */
@Serializable
data class ScoreTable(val castells: List<ScoreTableCastell>) {
    companion object {
        private const val RESOURCE = "/score-table-2026.json"

        fun bundled(): ScoreTable {
            val stream = checkNotNull(ScoreTable::class.java.getResourceAsStream(RESOURCE)) {
                "Falta el recurs $RESOURCE"
            }
            return Json.decodeFromString(serializer(), stream.use { it.readBytes().decodeToString() })
        }
    }
}
