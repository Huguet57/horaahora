package com.ahuguet.castellsenvena.feature.internalsettings.presentation

import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.domain.settings.HiddenSectionsPreferences
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class HiddenSectionsTest {
    private var clock = 1_000_000L

    @Test
    fun sevenQuickTapsShowTheHiddenSectionsAndSevenMoreHideThem() {
        val preferences = HiddenSectionsStub()
        val model = model(preferences)
        assertFalse(model.state.value.showsHiddenSections)

        assertEquals(List(6) { false }, tap(model, times = 6))
        assertFalse(model.state.value.showsHiddenSections)
        assertTrue(tapOnce(model))
        assertTrue(model.state.value.showsHiddenSections)
        assertTrue(preferences.isUnlocked)

        tap(model, times = 6)
        assertTrue(tapOnce(model))
        assertFalse(model.state.value.showsHiddenSections)
        assertFalse(preferences.isUnlocked)
    }

    @Test
    fun theVersionRowSaysWhatTheGestureDid() {
        val model = model(HiddenSectionsStub())

        assertEquals(List(6) { null }, List(6) { versionTap(model) })
        assertEquals("S'han activat Hora a Hora i Agenda", versionTap(model))
        assertEquals(List(6) { null }, List(6) { versionTap(model) })
        assertEquals("S'han amagat Hora a Hora i Agenda", versionTap(model))
    }

    @Test
    fun aPauseStartsTheSequenceAgain() {
        val model = model(HiddenSectionsStub())
        tap(model, times = 6)

        clock += 2_000
        assertFalse(tapOnce(model))
        tap(model, times = 5)
        assertFalse(model.state.value.showsHiddenSections)

        assertTrue(tapOnce(model))
        assertTrue(model.state.value.showsHiddenSections)
    }

    @Test
    fun usersWhoAlreadyGetNewsKeepTheHiddenSections() = runTest {
        val preferences = HiddenSectionsStub()
        val model = InternalSettingsModel(StatusStub(HourByHourNotificationStatus.ENABLED), hiddenSections = preferences)

        model.refreshNotificationStatus()

        assertEquals(listOf(true), preferences.resolvedDefaults)
        assertTrue(model.state.value.showsHiddenSections)
    }

    @Test
    fun everybodyElseStartsWithoutThem() = runTest {
        val preferences = HiddenSectionsStub()
        val model = InternalSettingsModel(StatusStub(HourByHourNotificationStatus.NOT_DETERMINED), hiddenSections = preferences)

        model.refreshNotificationStatus()

        assertEquals(listOf(false), preferences.resolvedDefaults)
        assertFalse(model.state.value.showsHiddenSections)
    }

    @Test
    fun withoutPreferencesTheSectionsStayHidden() {
        val model = model(preferences = null)

        assertEquals(List(7) { false }, tap(model, times = 7))
        assertFalse(model.state.value.showsHiddenSections)
    }

    private fun model(preferences: HiddenSectionsStub?) = InternalSettingsModel(
        notificationManager = StatusStub(HourByHourNotificationStatus.NOT_DETERMINED),
        hiddenSections = preferences,
        nowMillis = { clock },
    )

    private fun tap(model: InternalSettingsModel, times: Int): List<Boolean> = List(times) { tapOnce(model) }

    private fun tapOnce(model: InternalSettingsModel): Boolean {
        clock += 400
        return model.registerSecretTap()
    }

    private fun versionTap(model: InternalSettingsModel): String? {
        clock += 400
        return model.versionTapMessage()
    }
}

private class HiddenSectionsStub : HiddenSectionsPreferences {
    override var isUnlocked = false
        private set
    val resolvedDefaults = mutableListOf<Boolean>()

    override fun setUnlocked(unlocked: Boolean) {
        isUnlocked = unlocked
    }

    override fun resolveDefault(notificationsEnabled: Boolean) {
        resolvedDefaults += notificationsEnabled
        isUnlocked = notificationsEnabled
    }
}

private class StatusStub(private val status: HourByHourNotificationStatus) : HourByHourNotificationManaging {
    override val minimumInterest = NotificationInterestLevel.HIGH
    override suspend fun setMinimumInterest(value: NotificationInterestLevel) = Unit
    override suspend fun synchronizationPending() = false
    override suspend fun currentStatus() = status
    override suspend fun enable() = HourByHourNotificationStatus.ENABLED
    override suspend fun disable() = HourByHourNotificationStatus.DISABLED
    override suspend fun openSystemSettings() = Unit
}
