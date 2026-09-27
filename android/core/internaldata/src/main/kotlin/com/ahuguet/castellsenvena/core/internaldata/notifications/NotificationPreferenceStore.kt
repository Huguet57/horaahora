package com.ahuguet.castellsenvena.core.internaldata.notifications

import com.ahuguet.castellsenvena.core.data.notifications.NewsNotificationKeys
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel

class NotificationPreferenceStore(
    private val store: KeyValueStore,
    private val key: String = NewsNotificationKeys.MINIMUM_INTEREST,
) {
    val savedValue: NotificationInterestLevel?
        get() = store.getString(key)?.let(NotificationInterestLevel::fromWireValue)

    /**
     * New activations start with the most selective level. Users who already
     * received every notification keep doing so until they choose otherwise.
     */
    fun resolve(existingNotificationsEnabled: Boolean): NotificationInterestLevel =
        savedValue ?: (if (existingNotificationsEnabled) NotificationInterestLevel.LOW else NotificationInterestLevel.HIGH)
            .also(::save)

    fun save(value: NotificationInterestLevel) {
        store.putString(key, value.wireValue)
    }
}
