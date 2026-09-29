package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTableCastell
import kotlin.math.abs

/**
 * The rules of the Concurs that a comparison needs: the final score, the ranking with its
 * tie-breaks and the castells a colla may try in each round.
 *
 * It follows the Normes bàsiques and the Protocol de plaça of 2024, the latest complete ones,
 * with the 2026 change that only two carregats count.
 */
class ComparatorRules(table: ScoreTable) {
    val castells: Map<String, ScoreTableCastell> = table.castells.associateBy { it.notation }

    private val baseOf: Map<String, Int> = SAME_BASE_GROUPS
        .flatMapIndexed { index, group -> group.map { it to index } }
        .toMap()

    fun points(castell: PlannedCastell): Int {
        val entry = castells[castell.notation] ?: return 0
        return when (castell.outcome) {
            ComparatorOutcome.UNLOADED -> entry.unloaded
            ComparatorOutcome.LOADED -> entry.loaded
            ComparatorOutcome.ATTEMPT, ComparatorOutcome.DISMANTLED_ATTEMPT -> 0
        }
    }

    // Score

    /** The three best constructions, with at most two carregats and each castell once. */
    fun score(colla: ComparatorColla): ComparatorScore = score(colla.rounds, colla.penalties)

    private fun score(rounds: List<PlannedCastell?>, ownPenalties: Int = 0): ComparatorScore {
        val statuses: MutableList<RoundScore.Status> = rounds.map { castell ->
            when {
                castell == null -> RoundScore.Status.Empty
                castell.outcome.isAchieved -> RoundScore.Status.NotCounted(NotCountedReason.OUTSIDE_TOP_THREE)
                else -> RoundScore.Status.NotCounted(NotCountedReason.ATTEMPT)
            }
        }.toMutableList()

        // Each castell once, from its best round.
        val bestRound = mutableMapOf<String, Int>()
        rounds.forEachIndexed { index, castell ->
            if (castell == null || !castell.outcome.isAchieved) return@forEachIndexed
            val current = bestRound[castell.notation]
            if (current != null && points(rounds[current]!!) >= points(castell)) {
                statuses[index] = RoundScore.Status.NotCounted(NotCountedReason.REPEATED)
            } else {
                if (current != null) statuses[current] = RoundScore.Status.NotCounted(NotCountedReason.REPEATED)
                bestRound[castell.notation] = index
            }
        }

        val candidates = bestRound.values.sorted()
        var best = emptyList<Int>()
        var bestTotal = -1
        for (size in 1..minOf(3, candidates.size)) {
            for (group in combinations(candidates, size)) {
                val loaded = group.count { rounds[it]?.outcome == ComparatorOutcome.LOADED }
                if (loaded > 2) continue
                val total = group.sumOf { points(rounds[it]!!) }
                if (total > bestTotal) {
                    bestTotal = total
                    best = group
                }
            }
        }

        val loadedCounted = best.count { rounds[it]?.outcome == ComparatorOutcome.LOADED }
        for (index in candidates) {
            if (index in best) continue
            val isLoaded = rounds[index]?.outcome == ComparatorOutcome.LOADED
            val reason = if (isLoaded && loadedCounted >= 2) NotCountedReason.LOADED_LIMIT else NotCountedReason.OUTSIDE_TOP_THREE
            statuses[index] = RoundScore.Status.NotCounted(reason)
        }
        for (index in best) statuses[index] = RoundScore.Status.Counted

        // Using two rounds for a castell that counts is a double penalty.
        val twoRoundPenalties = best.sumOf { index ->
            val notation = rounds[index]!!.notation
            val tries = rounds.count { it?.notation == notation }
            if (tries >= 2) 2 else 0
        }

        val counted = best.map { points(rounds[it]!!) }.sortedDescending()
        return ComparatorScore(
            total = counted.sum(),
            rounds = rounds.zip(statuses) { castell, status -> RoundScore(castell?.let(::points) ?: 0, status) },
            penalties = ownPenalties + twoRoundPenalties,
            countedPoints = counted,
        )
    }

    private fun combinations(items: List<Int>, size: Int): List<List<Int>> {
        if (size == 0) return listOf(emptyList())
        if (items.size < size) return emptyList()
        return items.flatMapIndexed { index, item ->
            combinations(items.drop(index + 1), size - 1).map { listOf(item) + it }
        }
    }

    // Ranking

    /**
     * From the first to the last: points, then fewer penalties, then the best castell and the
     * second best.
     */
    fun ranking(colles: List<ComparatorColla>): List<ComparatorStanding> {
        val sorted = colles.map { it.id to score(it) }.sortedWith { lhs, rhs -> compareStandings(lhs.second, rhs.second) }
        return sorted.mapIndexed { index, (id, score) ->
            val next = sorted.getOrNull(index + 1)?.second
            ComparatorStanding(id, score, next?.let { tieBreak(score, over = it) })
        }
    }

    /** Negative when [a] ranks above [b]. */
    private fun compareStandings(a: ComparatorScore, b: ComparatorScore): Int = when {
        a.total != b.total -> b.total.compareTo(a.total)
        a.penalties != b.penalties -> a.penalties.compareTo(b.penalties)
        a.best != b.best -> b.best.compareTo(a.best)
        else -> b.second.compareTo(a.second)
    }

    private fun tieBreak(a: ComparatorScore, over: ComparatorScore): ComparatorStanding.TieBreak? = when {
        a.total != over.total -> null
        a.penalties != over.penalties -> ComparatorStanding.TieBreak.PENALTIES
        a.best != over.best -> ComparatorStanding.TieBreak.BEST_CASTELL
        a.second != over.second -> ComparatorStanding.TieBreak.SECOND_CASTELL
        else -> null
    }

    private val ComparatorScore.best: Int get() = countedPoints.getOrElse(0) { 0 }
    private val ComparatorScore.second: Int get() = countedPoints.getOrElse(1) { 0 }

    // Allowed attempts

    /**
     * Why the colla could not try [notation] in [round], given what it did in the rounds
     * before; `null` when it can.
     */
    fun restriction(notation: String, round: Int, colla: ComparatorColla): ComparatorRestriction? {
        val before = colla.rounds.take(round)
        val tries = before.filterNotNull().filter { it.notation == notation }
        if (tries.any { it.outcome == ComparatorOutcome.UNLOADED }) return ComparatorRestriction.AlreadyUnloaded
        if (tries.size >= 2) return ComparatorRestriction.TriedTwice

        val scoreBefore = score(before)
        val counted = before.zip(scoreBefore.rounds)
            .mapNotNull { (castell, score) -> castell.takeIf { score.status == RoundScore.Status.Counted } }
        val base = baseOf[notation]
        if (base != null) {
            val conflict = counted.firstOrNull { it.notation != notation && baseOf[it.notation] == base }
            if (conflict != null) return ComparatorRestriction.SameBase(conflict.notation)
        }

        if (round >= 3) {
            val achieved = before.filterNotNull().filter { it.outcome.isAchieved }
            if (achieved.size >= 3) {
                val loadedBefore = achieved.any { it.notation == notation && it.outcome == ComparatorOutcome.LOADED }
                val unloadedPoints = achieved.filter { it.outcome == ComparatorOutcome.UNLOADED }
                    .mapNotNull { castells[it.notation]?.unloaded }
                val candidate = castells[notation]?.unloaded ?: 0
                val improves = unloadedPoints.isEmpty() || candidate > unloadedPoints.min()
                if (!loadedBefore && !improves) return ComparatorRestriction.NoImprovement
            }
        }
        return null
    }

    // Steps

    /** The castells sorted by the points they would score with [outcome], from the fewest. */
    fun ladder(outcome: ComparatorOutcome): List<ScoreTableCastell> = castells.values.sortedWith(
        if (outcome == ComparatorOutcome.LOADED) {
            compareBy({ it.loaded }, { it.unloaded }, { it.notation })
        } else {
            compareBy({ it.unloaded }, { it.loaded }, { it.notation })
        },
    )

    /**
     * The next castell up (`direction > 0`) or down in points that the colla may try in that
     * round, with the same outcome.
     */
    fun step(castell: PlannedCastell, round: Int, colla: ComparatorColla, direction: Int): PlannedCastell? =
        neighbours(castell, round, colla, count = 1, direction = direction).firstOrNull()

    /** Up to [count] allowed neighbours, the closest first. */
    fun neighbours(castell: PlannedCastell, round: Int, colla: ComparatorColla, count: Int, direction: Int): List<PlannedCastell> {
        val ladder = ladder(castell.outcome)
        val index = ladder.indexOfFirst { it.notation == castell.notation }
        if (index < 0) return emptyList()
        val candidates = if (direction > 0) ladder.drop(index + 1) else ladder.take(index).asReversed()
        return candidates.asSequence()
            .filter { restriction(it.notation, round, colla) == null }
            .take(count)
            .map { PlannedCastell(it.notation, castell.outcome) }
            .toList()
    }

    // Summary

    /**
     * A scenario in two parts: who wins and by how much, "VELLA +450", and a line per colla
     * with its castells, "VIL 3d10fm 4d10fm 9d9fc", leaving out the colles without any.
     */
    fun summary(scenario: ComparatorScenario): ComparatorScenarioSummary {
        val ranking = ranking(scenario.colles)
        val first = ranking.firstOrNull()
        val title = if (first != null && first.score.total > 0) {
            val margin = if (ranking.size > 1) first.score.total - ranking[1].score.total else first.score.total
            val winner = scenario.colles.firstOrNull { it.id == first.collaId }?.shortName.orEmpty()
            if (margin > 0) "$winner +${formattedPoints(margin)}" else "Empat"
        } else {
            "Sense castells"
        }
        val lines = scenario.colles.mapNotNull { colla ->
            val castells = colla.rounds.mapNotNull { it?.shortNotation }
            if (castells.isEmpty()) null else (listOf(colla.shortName) + castells).joinToString(" ")
        }
        return ComparatorScenarioSummary(title, lines)
    }

    private companion object {
        /** The heights of one base, which cannot count together (Protocol de plaça, IX). */
        val SAME_BASE_GROUPS = listOf(
            listOf("Pde5", "Pde6", "Pde7f", "Pde8fm", "Pde9fmp"),
            listOf("2de6", "2de7", "2de8f", "2de9fm", "2de10fmp"),
            listOf("2de8sf", "2de9sm"),
            listOf("3de7", "3de8", "3de9f", "3de10fm"),
            listOf("3de7a", "3de8a", "3de9fa"),
            listOf("3de7s", "3de8s"),
            listOf("3de9sf", "3de10sm"),
            listOf("4de7", "4de8", "4de9f", "4de10fm"),
            listOf("4de7a", "4de8a", "4de9fa"),
            listOf("4de9sf", "4de10sm"),
            listOf("5de7", "5de8", "5de9f"),
            listOf("5de7a", "5de8a"),
            listOf("7de7", "7de8", "7de9f"),
            listOf("9de6", "9de7", "9de8", "9de9f"),
        )
    }
}

/** Who wins and by how much, and each colla's castells. */
data class ComparatorScenarioSummary(val title: String, val lines: List<String>)

/** "4.525", as the Concurs writes points, with a minus sign rather than a hyphen. */
fun formattedPoints(points: Int): String {
    val grouped = CatalanNumbers.grouped(abs(points))
    return if (points < 0) "−$grouped" else grouped
}

/** "+600", "−600" or "=". */
fun formattedMargin(margin: Int): String = when {
    margin > 0 -> "+" + formattedPoints(margin)
    margin < 0 -> formattedPoints(margin)
    else -> "="
}
