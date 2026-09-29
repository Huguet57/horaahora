package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import java.util.UUID
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** How a castell of a planned performance ends, as the Jurat of the Concurs reads it. */
@Serializable
enum class ComparatorOutcome(val shortLabel: String, val label: String) {
    @SerialName("unloaded")
    UNLOADED("D", "Descarregat"),

    @SerialName("loaded")
    LOADED("C", "Carregat"),

    @SerialName("attempt")
    ATTEMPT("I", "Intent"),

    @SerialName("dismantledAttempt")
    DISMANTLED_ATTEMPT("ID", "Intent desmuntat"),
    ;

    val isAchieved: Boolean get() = this == UNLOADED || this == LOADED
}

/** A castell a colla might try in one round, with how it ends. */
@Serializable
data class PlannedCastell(val notation: String, val outcome: ComparatorOutcome) {
    /**
     * The castell as castellers write it: "de" becomes "d", and the result follows unless it
     * is descarregat, "c" for carregat, "i" for intent and "id" for intent desmuntat.
     */
    val shortNotation: String
        get() {
            val suffix = when (outcome) {
                ComparatorOutcome.UNLOADED -> ""
                ComparatorOutcome.LOADED -> "c"
                ComparatorOutcome.ATTEMPT -> "i"
                ComparatorOutcome.DISMANTLED_ATTEMPT -> "id"
            }
            return notation.replace("de", "d") + suffix
        }
}

/** One colla of a comparison and the castell it tries in each of the five rounds. */
@Serializable
data class ComparatorColla(
    val id: String = UUID.randomUUID().toString(),
    val name: String,
    /** What the column shows when there are three or four colles. */
    val shortName: String,
    val rounds: List<PlannedCastell?> = List(ROUND_COUNT) { null },
    /**
     * The ones the Jurat would give it, which only break ties. Using two rounds for a castell
     * that counts adds its own, see [ComparatorScore.penalties].
     */
    val penalties: Int = 0,
) {
    /** The same colla with every round empty and no penalties. */
    fun cleared(): ComparatorColla = copy(rounds = List(ROUND_COUNT) { null }, penalties = 0)

    companion object {
        const val ROUND_COUNT = 5
    }
}

/** A whole "what if": every colla of the comparison and its performance. */
@Serializable
data class ComparatorScenario(
    val id: String = UUID.randomUUID().toString(),
    val colles: List<ComparatorColla>,
    /** Pinned in the Favorits section, on top of the rest. Scenarios saved before had none. */
    val isFavorite: Boolean = false,
    /** What the user called it; without one, the list names it after who wins. */
    val name: String? = null,
)

/** Why a round adds nothing to the final score. */
enum class NotCountedReason(val label: String) {
    ATTEMPT("intent"),

    /** The same castell counts from a better round. */
    REPEATED("repetit"),

    /** Only two carregats count in 2026. */
    LOADED_LIMIT("3r carregat"),
    OUTSIDE_TOP_THREE("fora de les 3"),
}

data class RoundScore(val points: Int, val status: Status) {
    sealed interface Status {
        data object Empty : Status

        data object Counted : Status

        data class NotCounted(val reason: NotCountedReason) : Status
    }

    val notCountedReason: NotCountedReason? get() = (status as? Status.NotCounted)?.reason
}

data class ComparatorScore(
    val total: Int,
    val rounds: List<RoundScore>,
    /** The colla's own plus two for each counted castell that took two rounds. */
    val penalties: Int,
    /** The counted points from the best castell down, to break ties. */
    val countedPoints: List<Int>,
)

/** What stops a colla from trying a castell in a round, from the Protocol de plaça. */
sealed interface ComparatorRestriction {
    val label: String

    data object AlreadyUnloaded : ComparatorRestriction {
        override val label = "ja descarregat"
    }

    data object TriedTwice : ComparatorRestriction {
        override val label = "ja intentat 2 cops"
    }

    /** Another height of the same base already counts. */
    data class SameBase(val notation: String) : ComparatorRestriction {
        override val label get() = "mateixa base que $notation"
    }

    /**
     * In the last two rounds, with three castells done, only a castell better than a
     * descarregat or a carregat to repeat is allowed.
     */
    data object NoImprovement : ComparatorRestriction {
        override val label = "no millora"
    }
}

data class ComparatorStanding(
    val collaId: String,
    val score: ComparatorScore,
    /** What puts it above the next colla when both have the same points. */
    val tieBreak: TieBreak?,
) {
    enum class TieBreak { PENALTIES, BEST_CASTELL, SECOND_CASTELL }
}
