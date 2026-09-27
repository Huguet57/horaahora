package com.ahuguet.castellsenvena.core.internaldata

import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsRetirement
import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsSystem
import com.ahuguet.castellsenvena.core.data.storage.InMemoryKeyValueStore
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.internaldata.notifications.NotificationPreferenceStore
import com.ahuguet.castellsenvena.core.internaldata.settings.KeyValueHiddenSectionsStore
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRemoteService
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRequest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlinx.coroutines.test.runTest

/**
 * The public app retires the news notifications of earlier versions when it finds one of the
 * settings they wrote. These stores still write them, in the internal app.
 */
class EarlierNewsNotificationSettingsTest {
    @Test
    fun thePublicAppRecognizesEverySettingTheseStoresWrite() = runTest {
        val writes: List<(KeyValueStore) -> Unit> = listOf(
            { NotificationPreferenceStore(it).save(NotificationInterestLevel.HIGH) },
            { KeyValueHiddenSectionsStore(it).setUnlocked(false) },
        )

        for (write in writes) {
            val remote = CountingRemote()
            val retirement = LegacyNewsNotificationsRetirement(
                store = InMemoryKeyValueStore().also(write),
                remoteService = remote,
                installationId = "installation-1",
                environment = "production",
                platform = "android",
                system = NoNotificationChannel,
            )

            retirement.retireIfNeeded()

            assertEquals(1, remote.unregistrations)
        }
    }

    private object NoNotificationChannel : LegacyNewsNotificationsSystem {
        override fun hadNewsNotifications() = false

        override fun stopShowingNewsNotifications() = Unit
    }

    private class CountingRemote : PushSubscriptionRemoteService {
        var unregistrations = 0

        override suspend fun register(request: PushSubscriptionRequest) = error("The retirement never subscribes")

        override suspend fun unregister(installationId: String, environment: String, platform: String) {
            unregistrations += 1
        }
    }
}
