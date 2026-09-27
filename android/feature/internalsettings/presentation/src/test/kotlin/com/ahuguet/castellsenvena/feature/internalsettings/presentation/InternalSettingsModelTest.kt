package com.ahuguet.castellsenvena.feature.internalsettings.presentation

import com.ahuguet.castellsenvena.core.common.UserFacingFailure
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsCredit
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class InternalSettingsModelTest {
    @Test
    fun thresholdCanChangeBeforeEnablingAndExposesPendingSync() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED)
        val model = InternalSettingsModel(manager)
        model.refreshNotificationStatus()
        assertEquals(NotificationInterestLevel.HIGH, model.state.value.minimumInterest)

        manager.pending = true
        model.setMinimumInterest(NotificationInterestLevel.MEDIUM)
        assertEquals(NotificationInterestLevel.MEDIUM, manager.minimumInterest)
        assertTrue(model.state.value.isNotificationSynchronizationPending)
        assertEquals(0, manager.enableCallCount)

        manager.pending = false
        model.refreshNotificationStatus()
        assertFalse(model.state.value.isNotificationSynchronizationPending)
    }

    @Test
    fun refreshExposesPendingPermissionAndShowsOnboarding() = runTest {
        val model = InternalSettingsModel(
            NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED),
            notificationOnboardingDismissed = false,
        )

        model.refreshNotificationStatus()

        assertEquals(HourByHourNotificationStatus.NOT_DETERMINED, model.state.value.notificationStatus)
        assertTrue(model.state.value.showsNotificationOnboarding)
        assertFalse(model.state.value.isUpdatingNotifications)
    }

    @Test
    fun enablingNotificationsRequestsPermission() = runTest {
        val manager = NotificationManagerStub(
            initialStatus = HourByHourNotificationStatus.NOT_DETERMINED,
            enabledStatus = HourByHourNotificationStatus.ENABLED,
        )
        val model = InternalSettingsModel(manager)

        model.setHourByHourNotificationsEnabled(true)

        assertEquals(1, manager.enableCallCount)
        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
        assertFalse(model.state.value.showsNotificationOnboarding)
    }

    @Test
    fun deniedPermissionIsExposedAsBlockedBySystem() = runTest {
        val model = InternalSettingsModel(
            NotificationManagerStub(
                initialStatus = HourByHourNotificationStatus.NOT_DETERMINED,
                enabledStatus = HourByHourNotificationStatus.DENIED,
            ),
        )

        model.setHourByHourNotificationsEnabled(true)

        assertEquals(HourByHourNotificationStatus.DENIED, model.state.value.notificationStatus)
        assertFalse(model.state.value.showsNotificationOnboarding)
        assertFalse(model.state.value.canToggleNotifications)
    }

    @Test
    fun disablingNotificationsUsesTheInjectedPort() = runTest {
        val manager = NotificationManagerStub(
            initialStatus = HourByHourNotificationStatus.ENABLED,
            disabledStatus = HourByHourNotificationStatus.DISABLED,
        )
        val model = InternalSettingsModel(manager)

        model.setHourByHourNotificationsEnabled(false)

        assertEquals(1, manager.disableCallCount)
        assertEquals(HourByHourNotificationStatus.DISABLED, model.state.value.notificationStatus)
    }

    @Test
    fun returningFromSystemSettingsRefreshesDeniedPermission() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.DENIED)
        val model = InternalSettingsModel(manager)
        model.refreshNotificationStatus()
        manager.currentStatusValue = HourByHourNotificationStatus.ENABLED

        model.refreshNotificationStatus()

        assertEquals(2, manager.currentStatusCallCount)
        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
    }

    @Test
    fun openingSystemSettingsUsesTheInjectedPort() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.DENIED)

        InternalSettingsModel(manager).openSystemSettings()

        assertEquals(1, manager.openSystemSettingsCallCount)
    }

    @Test
    fun onboardingCanBeDismissedAndPersistsTheChoice() {
        var persistedValue: Boolean? = null
        val model = InternalSettingsModel(
            NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED),
            notificationOnboardingDismissed = false,
            persistNotificationOnboardingDismissal = { persistedValue = it },
        )
        model.setNotificationStatusForTesting(HourByHourNotificationStatus.NOT_DETERMINED)

        model.handleNotificationOnboarding(NotificationOnboardingAction.DISMISS)

        assertFalse(model.state.value.showsNotificationOnboarding)
        assertEquals(true, persistedValue)
    }

    @Test
    fun onboardingConfigureActionOpensSettingsWithoutDismissingIt() {
        var didOpenSettings = false
        val model = InternalSettingsModel(NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED))
        model.setNotificationStatusForTesting(HourByHourNotificationStatus.NOT_DETERMINED)

        model.handleNotificationOnboarding(NotificationOnboardingAction.CONFIGURE) { didOpenSettings = true }

        assertTrue(didOpenSettings)
        assertTrue(model.state.value.showsNotificationOnboarding)
    }

    @Test
    fun failureKeepsThePreviousStatusAndShowsTheError() = runTest {
        val manager = NotificationManagerStub(
            initialStatus = HourByHourNotificationStatus.ENABLED,
            failure = StubFailure(),
        )
        val model = InternalSettingsModel(manager)
        model.refreshNotificationStatus()

        model.setHourByHourNotificationsEnabled(false)

        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
        assertEquals("No s'ha pogut canviar la configuració.", model.state.value.notificationErrorMessage)
        assertFalse(model.state.value.isUpdatingNotifications)
    }

    @Test
    fun unavailablePushCannotBeToggled() = runTest {
        val model = InternalSettingsModel(NotificationManagerStub(initialStatus = HourByHourNotificationStatus.UNAVAILABLE))

        model.refreshNotificationStatus()

        assertFalse(model.state.value.canToggleNotifications)
        assertFalse(model.state.value.showsNotificationOnboarding)
    }

    @Test
    fun theInternalSourcesAreCreditedWithTheirOfficialPages() {
        val sources = InternalSources(
            revistaCastellsUrl = "https://revistacastells.cat/castells-hora-a-hora/",
            elMonCastellerUrl = "https://www.elmoncasteller.cat/",
            ccccAgendaUrl = null,
        )

        assertEquals(
            listOf(
                SettingsCredit(
                    "Revista Castells",
                    "Font de l'Hora a Hora",
                    "https://revistacastells.cat/castells-hora-a-hora/",
                ),
                SettingsCredit(
                    "El Món Casteller",
                    "Notícies, opinió, entrevistes i cròniques de l'Hora a Hora",
                    "https://www.elmoncasteller.cat/",
                ),
                SettingsCredit("Coordinadora de Colles Castelleres de Catalunya (CCCC)", "Font de l'Agenda", null),
            ),
            sources.credits,
        )
    }

    private class StubFailure : Exception(), UserFacingFailure {
        override val userMessage = "No s'ha pogut canviar la configuració."
    }

    private class NotificationManagerStub(
        initialStatus: HourByHourNotificationStatus,
        private val enabledStatus: HourByHourNotificationStatus = HourByHourNotificationStatus.ENABLED,
        private val disabledStatus: HourByHourNotificationStatus = HourByHourNotificationStatus.DISABLED,
        private val failure: Exception? = null,
    ) : HourByHourNotificationManaging {
        override var minimumInterest = NotificationInterestLevel.HIGH
        var pending = false
        var currentStatusValue = initialStatus
        var currentStatusCallCount = 0
        var enableCallCount = 0
        var disableCallCount = 0
        var openSystemSettingsCallCount = 0

        override suspend fun setMinimumInterest(value: NotificationInterestLevel) {
            minimumInterest = value
        }

        override suspend fun synchronizationPending(): Boolean = pending

        override suspend fun currentStatus(): HourByHourNotificationStatus {
            currentStatusCallCount += 1
            return currentStatusValue
        }

        override suspend fun enable(): HourByHourNotificationStatus {
            enableCallCount += 1
            failure?.let { throw it }
            return enabledStatus
        }

        override suspend fun disable(): HourByHourNotificationStatus {
            disableCallCount += 1
            failure?.let { throw it }
            return disabledStatus
        }

        override suspend fun openSystemSettings() {
            openSystemSettingsCallCount += 1
        }
    }
}
