package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.settings.KeyValueHiddenSectionsStore
import com.ahuguet.castellsenvena.core.data.storage.InMemoryKeyValueStore
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class HiddenSectionsStoreTest {
    @Test
    fun newInstallationsStartWithTheSectionsHidden() {
        val store = KeyValueHiddenSectionsStore(InMemoryKeyValueStore())

        store.resolveDefault(notificationsEnabled = false)

        assertFalse(store.isUnlocked)
    }

    @Test
    fun usersWhoAlreadyGetNewsNotificationsKeepTheSections() {
        val store = KeyValueHiddenSectionsStore(InMemoryKeyValueStore())
        assertFalse(store.isUnlocked)

        store.resolveDefault(notificationsEnabled = true)

        assertTrue(store.isUnlocked)
    }

    @Test
    fun onlyTheFirstKnownNotificationStatusDecidesTheDefault() {
        val store = KeyValueHiddenSectionsStore(InMemoryKeyValueStore())
        store.resolveDefault(notificationsEnabled = false)

        store.resolveDefault(notificationsEnabled = true)

        assertFalse(store.isUnlocked)
    }

    @Test
    fun anExplicitChoiceWinsOverTheDefault() {
        val store = KeyValueHiddenSectionsStore(InMemoryKeyValueStore())
        store.setUnlocked(false)

        store.resolveDefault(notificationsEnabled = true)

        assertFalse(store.isUnlocked)
    }

    @Test
    fun theChoicePersistsAcrossLaunches() {
        val keyValueStore = InMemoryKeyValueStore()
        KeyValueHiddenSectionsStore(keyValueStore).setUnlocked(true)

        assertTrue(KeyValueHiddenSectionsStore(keyValueStore).isUnlocked)
    }
}
