package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsRetirement
import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsSystem
import com.ahuguet.castellsenvena.core.data.storage.InMemoryKeyValueStore
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRemoteService
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRequest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest

class LegacyNewsNotificationsRetirementTest {
    private val store = InMemoryKeyValueStore()
    private val remote = RecordingRemote()
    private val system = RecordingSystem()

    @Test
    fun aNewInstallationHasNothingToRetire() = runTest {
        val retirement = retirement()

        retirement.retireIfNeeded()
        retirement.retireIfNeeded()

        assertEquals(emptyList(), remote.unregistrations)
        assertEquals(0, system.stops)
        assertEquals(1, system.checks)
    }

    @Test
    fun anInstallationThatUsedNewsNotificationsStopsThemOnceAndLeavesTheBackend() = runTest {
        store.putBoolean("castells.hour-by-hour.notifications-enabled", true)
        val retirement = retirement()

        retirement.retireIfNeeded()
        retirement.retireIfNeeded()

        assertEquals(listOf(Triple("installation-1", "production", "android")), remote.unregistrations)
        assertEquals(1, system.stops)
    }

    @Test
    fun theOldSettingsNeverSubscribeTheDeviceAgain() = runTest {
        store.putBoolean("castells.hour-by-hour.notifications-enabled", true)
        store.putBoolean("castells.hour-by-hour.notification-permission-requested", true)
        store.putString("castells.hour-by-hour.minimum-interest.v1", "low")
        store.putBoolean("castells.hidden-sections.unlocked", true)

        retirement().retireIfNeeded()

        assertEquals(emptyList(), remote.registrations)
        assertEquals(1, remote.unregistrations.size)
    }

    @Test
    fun aFailedUnsubscriptionIsRetriedUntilTheBackendConfirmsIt() = runTest {
        store.putBoolean("castells.hour-by-hour.notifications-enabled", true)
        remote.unregisterFailures = 2
        val retirement = retirement()

        repeat(4) { retirement.retireIfNeeded() }

        assertEquals(3, remote.unregistrations.size)
        assertEquals(3, system.stops)
    }

    @Test
    fun everySettingThatAnEarlierVersionWroteCounts() = runTest {
        val earlierSettings: List<(KeyValueStore) -> Unit> = listOf(
            { it.putString("castells.hour-by-hour.minimum-interest.v1", "high") },
            { it.putBoolean("castells.hidden-sections.unlocked", false) },
            { it.putBoolean("castells.hour-by-hour.notifications-enabled", false) },
            { it.putBoolean("castells.hour-by-hour.notification-permission-requested", true) },
            { it.putBoolean("castells.hour-by-hour.notification-onboarding-dismissed", true) },
        )

        for (write in earlierSettings) {
            val store = InMemoryKeyValueStore().also(write)
            val remote = RecordingRemote()

            retirement(store, remote).retireIfNeeded()

            assertEquals(1, remote.unregistrations.size)
        }
    }

    @Test
    fun theNotificationChannelOfAnEarlierVersionAlsoCounts() = runTest {
        system.hadNewsNotifications = true

        retirement().retireIfNeeded()

        assertEquals(1, remote.unregistrations.size)
        assertEquals(1, system.stops)
    }

    @Test
    fun launchesThatOverlapUnsubscribeOnce() = runTest {
        system.hadNewsNotifications = true
        remote.holdUnregistrations = true
        val retirement = retirement()

        val launches = List(2) { launch { retirement.retireIfNeeded() } }
        remote.unregistrationStarted.await()
        remote.releaseUnregistrations()
        launches.joinAll()

        assertEquals(1, remote.unregistrations.size)
        assertEquals(1, system.stops)
    }

    private fun retirement(
        store: KeyValueStore = this.store,
        remote: PushSubscriptionRemoteService = this.remote,
    ) = LegacyNewsNotificationsRetirement(
        store = store,
        remoteService = remote,
        installationId = "installation-1",
        environment = "production",
        platform = "android",
        system = system,
    )

    private class RecordingSystem : LegacyNewsNotificationsSystem {
        var hadNewsNotifications = false
        var checks = 0
        var stops = 0

        override fun hadNewsNotifications(): Boolean {
            checks += 1
            return hadNewsNotifications
        }

        override fun stopShowingNewsNotifications() {
            stops += 1
        }
    }

    private class RecordingRemote : PushSubscriptionRemoteService {
        val registrations = mutableListOf<PushSubscriptionRequest>()
        val unregistrations = mutableListOf<Triple<String, String, String>>()
        var unregisterFailures = 0
        var holdUnregistrations = false
        val unregistrationStarted = CompletableDeferred<Unit>()
        private val unregistrationsReleased = CompletableDeferred<Unit>()

        fun releaseUnregistrations() {
            unregistrationsReleased.complete(Unit)
        }

        override suspend fun register(request: PushSubscriptionRequest) {
            registrations += request
        }

        override suspend fun unregister(installationId: String, environment: String, platform: String) {
            unregistrations += Triple(installationId, environment, platform)
            if (holdUnregistrations) {
                unregistrationStarted.complete(Unit)
                unregistrationsReleased.await()
            }
            if (unregisterFailures > 0) {
                unregisterFailures -= 1
                throw offline()
            }
        }
    }
}
