package com.ahuguet.castellsenvena.feature.calculator.presentation

import java.time.Duration
import java.time.Instant

/** "29 min", "1 h i 1 min", "2 dies i 9 h": at most two non-zero units. */
object ConversationAgeFormatter {
    fun format(from: Instant, relativeTo: Instant): String {
        val elapsedSeconds = maxOf(0L, Duration.between(from, relativeTo).seconds)
        if (elapsedSeconds < 60) return "menys d’1 min"

        val days = elapsedSeconds / 86_400
        val hours = elapsedSeconds / 3_600 % 24
        val minutes = elapsedSeconds / 60 % 60
        val components = buildList {
            if (days > 0) add(if (days == 1L) "1 dia" else "$days dies")
            if (hours > 0) add("$hours h")
            if (minutes > 0) add("$minutes min")
        }
        return components.take(2).joinToString(" i ")
    }
}
