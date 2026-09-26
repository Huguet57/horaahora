package com.ahuguet.castellsenvena.feature.settings.presentation

import com.ahuguet.castellsenvena.core.common.UserFacingFailure
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import java.net.URLDecoder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class SettingsModelTest {
    @Test
    fun thresholdCanChangeBeforeEnablingAndExposesPendingSync() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED)
        val model = SettingsModel(manager)
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
        val model = SettingsModel(
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
        val model = SettingsModel(manager)

        model.setHourByHourNotificationsEnabled(true)

        assertEquals(1, manager.enableCallCount)
        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
        assertFalse(model.state.value.showsNotificationOnboarding)
    }

    @Test
    fun deniedPermissionIsExposedAsBlockedBySystem() = runTest {
        val model = SettingsModel(
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
        val model = SettingsModel(manager)

        model.setHourByHourNotificationsEnabled(false)

        assertEquals(1, manager.disableCallCount)
        assertEquals(HourByHourNotificationStatus.DISABLED, model.state.value.notificationStatus)
    }

    @Test
    fun returningFromSystemSettingsRefreshesDeniedPermission() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.DENIED)
        val model = SettingsModel(manager)
        model.refreshNotificationStatus()
        manager.currentStatusValue = HourByHourNotificationStatus.ENABLED

        model.refreshNotificationStatus()

        assertEquals(2, manager.currentStatusCallCount)
        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
    }

    @Test
    fun openingSystemSettingsUsesTheInjectedPort() = runTest {
        val manager = NotificationManagerStub(initialStatus = HourByHourNotificationStatus.DENIED)

        SettingsModel(manager).openSystemSettings()

        assertEquals(1, manager.openSystemSettingsCallCount)
    }

    @Test
    fun onboardingCanBeDismissedAndPersistsTheChoice() {
        var persistedValue: Boolean? = null
        val model = SettingsModel(
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
        val model = SettingsModel(NotificationManagerStub(initialStatus = HourByHourNotificationStatus.NOT_DETERMINED))
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
        val model = SettingsModel(manager)
        model.refreshNotificationStatus()

        model.setHourByHourNotificationsEnabled(false)

        assertEquals(HourByHourNotificationStatus.ENABLED, model.state.value.notificationStatus)
        assertEquals("No s'ha pogut canviar la configuració.", model.state.value.notificationErrorMessage)
        assertFalse(model.state.value.isUpdatingNotifications)
    }

    @Test
    fun unavailablePushCannotBeToggled() = runTest {
        val model = SettingsModel(NotificationManagerStub(initialStatus = HourByHourNotificationStatus.UNAVAILABLE))

        model.refreshNotificationStatus()

        assertFalse(model.state.value.canToggleNotifications)
        assertFalse(model.state.value.showsNotificationOnboarding)
    }

    @Test
    fun privacyUrlIsBuiltBelowTheInjectedApiBaseUrl() {
        assertEquals(
            "https://example.test/service/privacy",
            configuration(apiBaseUrl = "https://example.test/service/").privacyUrl,
        )
        assertEquals("https://example.test/privacy", configuration(apiBaseUrl = "https://example.test").privacyUrl)
    }

    @Test
    fun supportEmailUrlIncludesEditableEncodedMetadata() {
        val url = configuration(
            supportEmail = "suport+castells@example.test",
            appVersion = "2.4",
            buildNumber = "91",
            technicalIdentifier = "ABC 123/ç",
        ).supportEmailUrl

        assertTrue(url.startsWith("mailto:suport+castells@example.test?"))
        val query = url.substringAfter('?').split('&').associate { parameter ->
            parameter.substringBefore('=') to URLDecoder.decode(parameter.substringAfter('='), Charsets.UTF_8)
        }
        assertEquals("Suport Castells en vena", query["subject"])
        assertTrue(query.getValue("body").contains("Versió: 2.4 (91)"))
        assertTrue(query.getValue("body").contains("Identificador tècnic: ABC 123/ç"))
        assertTrue(url.contains("%0A"))
        assertTrue(url.contains("%C3%A7"))
        assertFalse(url.contains(' '))
        assertEquals("Versió 2.4 (91)", configuration(appVersion = "2.4", buildNumber = "91").versionAndBuild)
    }

    private fun configuration(
        apiBaseUrl: String = "https://example.test",
        supportEmail: String = "support@example.test",
        appVersion: String = "1.0",
        buildNumber: String = "1",
        technicalIdentifier: String = "test-id",
    ) = SettingsConfiguration(
        apiBaseUrl = apiBaseUrl,
        supportEmail = supportEmail,
        appName = "Castells en vena",
        appVersion = appVersion,
        buildNumber = buildNumber,
        technicalIdentifier = technicalIdentifier,
        revistaCastellsUrl = "https://revistacastells.cat/castells-hora-a-hora/",
        elMonCastellerUrl = "https://www.elmoncasteller.cat/",
        ccccAgendaUrl = "https://castellscat.cat/public/ca/agenda",
        concursCastellsUrl = null,
    )

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
