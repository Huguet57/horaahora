package com.ahuguet.castellsenvena.feature.internalsettings.presentation

/** Seven quick taps on the version in Ajustos show or hide the sections hidden by default. */
internal class SecretTapSequence {
    private var count = 0
    private var lastTapMillis: Long? = null

    /** Whether this tap, at [nowMillis], completes the sequence. */
    fun register(nowMillis: Long): Boolean {
        val last = lastTapMillis
        count = if (last != null && nowMillis - last <= MAXIMUM_PAUSE_MILLIS) count + 1 else 1
        lastTapMillis = nowMillis
        if (count < REQUIRED_TAPS) return false
        count = 0
        lastTapMillis = null
        return true
    }

    private companion object {
        const val REQUIRED_TAPS = 7

        /** A longer pause between two taps starts the sequence again. */
        const val MAXIMUM_PAUSE_MILLIS = 1_500L
    }
}
