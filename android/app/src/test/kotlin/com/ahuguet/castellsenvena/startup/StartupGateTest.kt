package com.ahuguet.castellsenvena.startup

import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class StartupGateTest {
    private var clock = 1_000L
    private val gate = StartupGate(now = { clock })

    @Test
    fun staysForTheMinimumSoItNeverFlashes() {
        clock += 100
        assertTrue(gate.keepsLaunchScreen())

        clock += 150
        assertFalse(gate.keepsLaunchScreen())
    }

    @Test
    fun onceReleasedItNeverComesBack() {
        clock += 300
        assertFalse(gate.keepsLaunchScreen())

        clock = 1_000L
        assertFalse(gate.keepsLaunchScreen())
    }
}
