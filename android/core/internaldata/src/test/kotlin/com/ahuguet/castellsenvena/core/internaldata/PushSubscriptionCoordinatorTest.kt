package com.ahuguet.castellsenvena.core.internaldata

import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection.Mode
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.internaldata.notifications.PushSubscriptionCoordinator
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRemoteService
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRequest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest

class PushSubscriptionCoordinatorTest {
    @Test
    fun enablingWaitsForTheDeviceTokenAndThenRegistersIt() = runTest {
        val remote = RecordingRemote()
        val coordinator = coordinator(remote)

        coordinator.setEnabled(true)
        assertEquals(0, remote.requests.size)
        assertTrue(coordinator.isSynchronizationPending())

        coordinator.didReceiveDeviceToken("ab12")

        val registration = remote.requests.single()
        assertEquals("installation-1", registration.installationId)
        assertEquals("ab12", registration.deviceToken)
        assertEquals("1.0 (3)", registration.appVersion)
        assertEquals("ca-ES", registration.locale)
        assertEquals("development", registration.environment)
        assertEquals("android", registration.platform)
        assertFalse(coordinator.synchronizationPending.value)
    }

    @Test
    fun tokenRotationRegistersTheNewTokenOnlyOnce() = runTest {
        val remote = RecordingRemote()
        val coordinator = coordinator(remote)
        coordinator.setEnabled(true)

        coordinator.didReceiveDeviceToken("first")
        coordinator.didReceiveDeviceToken("second")
        coordinator.didReceiveDeviceToken("second")

        assertEquals(listOf("first", "second"), remote.requests.map { it.deviceToken })
    }

    @Test
    fun disablingUnregistersAndAFailureIsRetriedOnTheNextSynchronization() = runTest {
        val remote = RecordingRemote(unregisterFailures = 1)
        val coordinator = coordinator(remote)

        coordinator.setEnabled(false)
        assertTrue(coordinator.synchronizationPending.value)
        coordinator.setEnabled(false)
        coordinator.setEnabled(false)

        assertEquals(2, remote.unregistrations)
        assertFalse(coordinator.synchronizationPending.value)
    }

    @Test
    fun preferencesStayLocalUntilNotificationsAreEnabledOrDisabled() = runTest {
        val remote = RecordingRemote()
        val coordinator = coordinator(remote)

        coordinator.didReceiveDeviceToken("token")
        coordinator.setPreferences(NotificationInterestLevel.LOW, NotificationGroupSelection())

        assertTrue(remote.requests.isEmpty())
        assertFalse(coordinator.isSynchronizationPending())
    }

    @Test
    fun changingPreferencesWithTheSameTokenRegistersAgainAndRetriesFailures() = runTest {
        val remote = RecordingRemote()
        val coordinator = coordinator(remote)
        coordinator.setEnabled(true)
        coordinator.didReceiveDeviceToken("token")
        remote.failNextRegistration = true

        coordinator.setPreferences(
            NotificationInterestLevel.MEDIUM,
            NotificationGroupSelection(Mode.CUSTOM, listOf("Minyons")),
        )
        assertTrue(coordinator.isSynchronizationPending())
        coordinator.setEnabled(true)

        assertFalse(coordinator.isSynchronizationPending())
        assertEquals(3, remote.requests.size)
        assertEquals(NotificationInterestLevel.MEDIUM, remote.requests.last().minimumInterest)
        assertEquals(listOf("minyons"), remote.requests.last().groupSelection.keys)
    }

    @Test
    fun concurrentChangesAreSerializedAndTheLatestSelectionWins() = runTest {
        val remote = RecordingRemote(suspendFirstRegistration = true)
        val coordinator = coordinator(remote)
        coordinator.setEnabled(true)

        val first = launch { coordinator.didReceiveDeviceToken("token") }
        remote.firstRegistrationStarted.await()
        coordinator.setPreferences(NotificationInterestLevel.LOW, NotificationGroupSelection())
        coordinator.setPreferences(
            NotificationInterestLevel.MEDIUM,
            NotificationGroupSelection(Mode.CUSTOM, listOf("a")),
        )
        remote.releaseFirstRegistration()
        first.join()

        assertEquals(
            listOf(NotificationInterestLevel.HIGH, NotificationInterestLevel.MEDIUM),
            remote.requests.map { it.minimumInterest },
        )
        assertFalse(coordinator.isSynchronizationPending())
    }

    @Test
    fun disablingWhileARegistrationIsInFlightEndsUnregistered() = runTest {
        val remote = RecordingRemote(suspendFirstRegistration = true)
        val coordinator = coordinator(remote)
        coordinator.setEnabled(true)

        val first = launch { coordinator.didReceiveDeviceToken("token") }
        remote.firstRegistrationStarted.await()
        coordinator.setEnabled(false)
        remote.releaseFirstRegistration()
        first.join()

        assertEquals(1, remote.unregistrations)
        assertFalse(coordinator.isSynchronizationPending())
    }

    private fun coordinator(remote: PushSubscriptionRemoteService) = PushSubscriptionCoordinator(
        remoteService = remote,
        installationId = "installation-1",
        appVersion = "1.0 (3)",
        locale = "ca-ES",
        environment = "development",
        platform = "android",
    )

    private class RecordingRemote(
        private var unregisterFailures: Int = 0,
        private val suspendFirstRegistration: Boolean = false,
    ) : PushSubscriptionRemoteService {
        val requests = mutableListOf<PushSubscriptionRequest>()
        var unregistrations = 0
        var failNextRegistration = false
        val firstRegistrationStarted = CompletableDeferred<Unit>()
        private val firstRegistrationReleased = CompletableDeferred<Unit>()

        fun releaseFirstRegistration() {
            firstRegistrationReleased.complete(Unit)
        }

        override suspend fun register(request: PushSubscriptionRequest) {
            requests += request
            if (suspendFirstRegistration && requests.size == 1) {
                firstRegistrationStarted.complete(Unit)
                firstRegistrationReleased.await()
            }
            if (failNextRegistration) {
                failNextRegistration = false
                throw offline()
            }
        }

        override suspend fun unregister(installationId: String, environment: String, platform: String) {
            unregistrations += 1
            if (unregisterFailures > 0) {
                unregisterFailures -= 1
                throw offline()
            }
        }
    }
}
