package com.ahuguet.castellsenvena.startup

/**
 * Keeps the launch screen up for at least [minimumMillis], so it never just
 * flashes. Once released it stays released, also when the activity is recreated.
 */
class StartupGate(
    private val now: () -> Long,
    private val minimumMillis: Long = 250,
) {
    private val startedAt = now()
    private var isReleased = false

    fun keepsLaunchScreen(): Boolean {
        if (isReleased) return false
        val keeps = now() - startedAt < minimumMillis
        if (!keeps) isReleased = true
        return keeps
    }
}
