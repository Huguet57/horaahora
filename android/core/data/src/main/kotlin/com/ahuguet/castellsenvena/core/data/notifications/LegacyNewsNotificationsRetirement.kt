package com.ahuguet.castellsenvena.core.data.notifications

import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRemoteService
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** What an earlier version of the app set up in the system for news notifications. */
interface LegacyNewsNotificationsSystem {
    /** Whether the system still remembers news notifications from an earlier version. */
    fun hadNewsNotifications(): Boolean

    /** Stops the system from showing them, including those already shown. */
    fun stopShowingNewsNotifications()
}

/**
 * The public app has no news notifications. An installation that used them in an earlier
 * version may still be subscribed on the backend, and the system would keep showing what
 * arrives. This stops both: it removes them from the system and unsubscribes the
 * installation, and tries again at every launch until the backend confirms it. It never
 * subscribes anything, whatever the earlier version's settings say.
 */
class LegacyNewsNotificationsRetirement(
    private val store: KeyValueStore,
    private val remoteService: PushSubscriptionRemoteService,
    private val installationId: String,
    private val environment: String,
    private val platform: String,
    private val system: LegacyNewsNotificationsSystem,
) {
    private val mutex = Mutex()

    suspend fun retireIfNeeded() {
        mutex.withLock {
            if (store.getBoolean(RETIRED_KEY) == true) return
            if (!hadNewsNotifications()) {
                store.putBoolean(RETIRED_KEY, true)
                return
            }
            system.stopShowingNewsNotifications()
            val unsubscribed = try {
                remoteService.unregister(installationId, environment, platform)
                true
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (_: Exception) {
                // Offline or a server error: the next launch tries again.
                false
            }
            if (unsubscribed) store.putBoolean(RETIRED_KEY, true)
        }
    }

    /** An earlier version with news notifications left one of its settings, or their channel. */
    private fun hadNewsNotifications(): Boolean =
        store.getString(NewsNotificationKeys.MINIMUM_INTEREST) != null ||
            EARLIER_FLAGS.any { store.getBoolean(it) != null } ||
            system.hadNewsNotifications()

    private companion object {
        const val RETIRED_KEY = "castells.news-notifications.retired.v1"
        val EARLIER_FLAGS = listOf(
            NewsNotificationKeys.ENABLED,
            NewsNotificationKeys.PERMISSION_REQUESTED,
            NewsNotificationKeys.ONBOARDING_DISMISSED,
            NewsNotificationKeys.SECTIONS_UNLOCKED,
        )
    }
}
