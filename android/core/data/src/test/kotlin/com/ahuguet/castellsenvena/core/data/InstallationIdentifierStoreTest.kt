package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.storage.InMemoryKeyValueStore
import com.ahuguet.castellsenvena.core.data.storage.InstallationIdentifierStore
import kotlin.test.Test
import kotlin.test.assertEquals

class InstallationIdentifierStoreTest {
    @Test
    fun theInstallationIdentifierIsCreatedOnce() {
        val keyValueStore = InMemoryKeyValueStore()
        var created = 0
        val store = InstallationIdentifierStore(keyValueStore) { "ID-${++created}" }

        assertEquals("ID-1", store.currentIdentifier())
        assertEquals("ID-1", InstallationIdentifierStore(keyValueStore) { "other" }.currentIdentifier())
        assertEquals(1, created)
    }
}
