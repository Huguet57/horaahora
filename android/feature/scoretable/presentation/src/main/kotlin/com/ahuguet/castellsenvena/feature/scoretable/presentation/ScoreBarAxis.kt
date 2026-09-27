package com.ahuguet.castellsenvena.feature.scoretable.presentation

/**
 * The points a bar spans, following the part of the table on screen.
 *
 * The smallest value on screen keeps [LEADING_FRACTION] of the bar and the largest
 * fills it, so that neighbouring castells differ visibly. A castell leaving or
 * entering the screen counts in proportion to its weight, so the scale moves
 * smoothly while scrolling.
 */
data class ScoreBarAxis(val lowerBound: Double, val upperBound: Double) {
    /** How much of the bar [points] fill, between 0 and 1. */
    fun fraction(points: Int): Double {
        val span = upperBound - lowerBound
        if (span <= 0) return 1.0
        return ((points - lowerBound) / span).coerceIn(0.0, 1.0)
    }

    companion object {
        const val LEADING_FRACTION = 0.06

        /** Castells weighing at least this count as whole; the rest only pull the scale partway. */
        private const val WHOLE = 0.999

        /** The whole table, until the screen reports which castells show. */
        fun forCastells(castells: List<ScoreTableCastell>): ScoreBarAxis = spanning(
            lowest = (castells.minOfOrNull { it.lowestPoints } ?: 0).toDouble(),
            highest = (castells.maxOfOrNull { it.highestPoints } ?: 0).toDouble(),
        )

        /** Scales the bars to the castells on screen, each with its weight from [weight]. */
        fun forVisible(visible: List<Pair<ScoreTableCastell, Double>>): ScoreBarAxis? {
            val shown = visible.filter { (_, weight) -> weight > 0 }
            if (shown.isEmpty()) return null
            val whole = shown.filter { (_, weight) -> weight >= WHOLE }
            val anchors = whole.ifEmpty { shown }
            val baseHighest = anchors.maxOf { (castell, _) -> castell.highestPoints }.toDouble()
            val baseLowest = anchors.minOf { (castell, _) -> castell.lowestPoints }.toDouble()
            var highest = baseHighest
            var lowest = baseLowest
            if (whole.isNotEmpty()) {
                for ((castell, weight) in shown) {
                    if (weight >= WHOLE) continue
                    highest = maxOf(highest, baseHighest + (castell.highestPoints - baseHighest) * weight)
                    lowest = minOf(lowest, baseLowest + (castell.lowestPoints - baseLowest) * weight)
                }
            }
            return spanning(lowest, highest)
        }

        /**
         * How much a castell counts in the scale, from where the top of its row is on
         * screen. A row in the window counts whole; outside it counts less and less
         * over [fadeAbove] or [fadeBelow] pixels, while it passes under the group
         * header or leaves at the bottom. A pixel of slack keeps rounding from pushing
         * a row at rest out of the window.
         */
        fun weight(rowTop: Float, windowTop: Float, windowBottom: Float, fadeAbove: Float, fadeBelow: Float): Double {
            val top = windowTop - 1f
            if (rowTop in top..windowBottom) return 1.0
            val above = rowTop < top
            val distance = if (above) top - rowTop else rowTop - windowBottom
            val fade = if (above) fadeAbove else fadeBelow
            if (fade <= 0f) return 0.0
            return (1.0 - distance / fade).coerceAtLeast(0.0)
        }

        private fun spanning(lowest: Double, highest: Double): ScoreBarAxis {
            val span = maxOf(highest - lowest, 1.0)
            return ScoreBarAxis(
                lowerBound = lowest - span * LEADING_FRACTION / (1 - LEADING_FRACTION),
                upperBound = highest,
            )
        }
    }
}

private val ScoreTableCastell.highestPoints: Int get() = maxOf(loaded, unloaded)
private val ScoreTableCastell.lowestPoints: Int get() = minOf(loaded, unloaded)
