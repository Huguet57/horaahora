package com.ahuguet.castellsenvena.startup

/**
 * Keeps the launch screen up until the first Hora a Hora page is ready: at
 * least [minimumMillis], so it never flashes, and at most [maximumMillis].
 * Once released it stays released, also when the activity is recreated.
 */
class StartupGate(
    private val now: () -> Long,
    private val minimumMillis: Long = 250,
    private val maximumMillis: Long = 2_000,
) {
    private val startedAt = now()
    private var isReleased = false

    fun keepsLaunchScreen(initialLoadHasCompleted: Boolean): Boolean {
        if (isReleased) return false
        val elapsed = now() - startedAt
        val keeps = elapsed < maximumMillis && (elapsed < minimumMillis || !initialLoadHasCompleted)
        if (!keeps) isReleased = true
        return keeps
    }
}
