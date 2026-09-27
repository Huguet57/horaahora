package com.ahuguet.castellsenvena.core.internaldata.settings

import com.ahuguet.castellsenvena.core.data.notifications.NewsNotificationKeys
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.settings.HiddenSectionsPreferences

class KeyValueHiddenSectionsStore(private val store: KeyValueStore) : HiddenSectionsPreferences {
    override val isUnlocked: Boolean
        get() = store.getBoolean(NewsNotificationKeys.SECTIONS_UNLOCKED) ?: false

    override fun setUnlocked(unlocked: Boolean) {
        store.putBoolean(NewsNotificationKeys.SECTIONS_UNLOCKED, unlocked)
    }

    override fun resolveDefault(notificationsEnabled: Boolean) {
        if (store.getBoolean(NewsNotificationKeys.SECTIONS_UNLOCKED) == null) store.putBoolean(NewsNotificationKeys.SECTIONS_UNLOCKED, notificationsEnabled)
    }
}
