package com.ahuguet.castellsenvena.core.data.settings

import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.settings.HiddenSectionsPreferences

class KeyValueHiddenSectionsStore(private val store: KeyValueStore) : HiddenSectionsPreferences {
    override val isUnlocked: Boolean
        get() = store.getBoolean(KEY) ?: false

    override fun setUnlocked(unlocked: Boolean) {
        store.putBoolean(KEY, unlocked)
    }

    override fun resolveDefault(notificationsEnabled: Boolean) {
        if (store.getBoolean(KEY) == null) store.putBoolean(KEY, notificationsEnabled)
    }

    private companion object {
        const val KEY = "castells.hidden-sections.unlocked"
    }
}
