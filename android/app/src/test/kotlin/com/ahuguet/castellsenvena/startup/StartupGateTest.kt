package com.ahuguet.castellsenvena.startup

import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class StartupGateTest {
    private var clock = 1_000L
    private val gate = StartupGate(now = { clock })

    @Test
    fun staysAtLeastTheMinimumEvenWhenTheFeedIsReady() {
        clock += 100
        assertTrue(gate.keepsLaunchScreen(initialLoadHasCompleted = true))

        clock += 150
        assertFalse(gate.keepsLaunchScreen(initialLoadHasCompleted = true))
    }

    @Test
    fun waitsForTheFeedUntilTheMaximum() {
        clock += 1_999
        assertTrue(gate.keepsLaunchScreen(initialLoadHasCompleted = false))

        clock += 1
        assertFalse(gate.keepsLaunchScreen(initialLoadHasCompleted = false))
    }

    @Test
    fun onceReleasedItNeverComesBack() {
        clock += 300
        assertFalse(gate.keepsLaunchScreen(initialLoadHasCompleted = true))

        assertFalse(gate.keepsLaunchScreen(initialLoadHasCompleted = false))
    }
}
