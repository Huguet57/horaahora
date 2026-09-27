package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.agenda.KeyValueAgendaFilterStore
import com.ahuguet.castellsenvena.core.data.groups.RemoteGroupDirectoryRepository
import com.ahuguet.castellsenvena.core.data.notifications.NotificationPreferenceStore
import com.ahuguet.castellsenvena.core.data.storage.InMemoryKeyValueStore
import com.ahuguet.castellsenvena.core.data.storage.InstallationIdentifierStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterState
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import com.ahuguet.castellsenvena.core.domain.groups.CastellerGroupDirectory
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.network.service.GroupDirectoryRemoteService
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class PreferencesTest {
    @Test
    fun newUsersDefaultToHighAndExistingEnabledUsersKeepLow() {
        val store = InMemoryKeyValueStore()
        assertEquals(NotificationInterestLevel.HIGH, NotificationPreferenceStore(store, "new").resolve(false))

        val old = NotificationPreferenceStore(store, "old")
        assertEquals(NotificationInterestLevel.LOW, old.resolve(existingNotificationsEnabled = true))
        old.save(NotificationInterestLevel.MEDIUM)

        val restored = NotificationPreferenceStore(store, "old")
        assertEquals(NotificationInterestLevel.MEDIUM, restored.resolve(existingNotificationsEnabled = true))
    }

    @Test
    fun onlyFollowingChangesNotifyTheNotificationBridge() {
        val store = KeyValueAgendaFilterStore(InMemoryKeyValueStore())
        val changes = mutableListOf<AgendaGroupSelection>()
        store.onSelectionChange = { changes += it }

        var state = store.load()
        state = state.copy(featuredGroupKeys = setOf("a"))
        store.save(state)
        assertTrue(changes.isEmpty())

        state = state.copy(selection = AgendaGroupSelection.Custom(setOf("a")))
        store.save(state)
        store.save(state)
        assertEquals(listOf<AgendaGroupSelection>(AgendaGroupSelection.Custom(setOf("a"))), changes)

        state = state.copy(selection = AgendaGroupSelection.All)
        store.save(state)
        assertEquals(listOf(AgendaGroupSelection.Custom(setOf("a")), AgendaGroupSelection.All), changes)
    }

    @Test
    fun theAgendaFilterSurvivesARestart() {
        val keyValueStore = InMemoryKeyValueStore()
        val state = AgendaFilterState(
            selection = AgendaGroupSelection.Custom(setOf("colla b", "colla a")),
            featuredGroupKeys = setOf("colla b"),
            cachedGroups = listOf("Colla A", "Colla B"),
            directoryRevision = "2026-07-25",
        )

        KeyValueAgendaFilterStore(keyValueStore).save(state)

        assertEquals(state, KeyValueAgendaFilterStore(keyValueStore).load())
    }

    @Test
    fun unreadableFiltersFallBackToFollowingEveryGroup() {
        val keyValueStore = InMemoryKeyValueStore()
        keyValueStore.putString(KeyValueAgendaFilterStore.DEFAULT_KEY, "{not json")

        assertEquals(AgendaFilterState(), KeyValueAgendaFilterStore(keyValueStore).load())
    }

    @Test
    fun theInstallationIdentifierIsCreatedOnce() {
        val keyValueStore = InMemoryKeyValueStore()
        var created = 0
        val store = InstallationIdentifierStore(keyValueStore) { "ID-${++created}" }

        assertEquals("ID-1", store.currentIdentifier())
        assertEquals("ID-1", InstallationIdentifierStore(keyValueStore) { "other" }.currentIdentifier())
        assertEquals(1, created)
    }

    @Test
    fun groupDirectoryDelegatesTheRefreshPolicyToTheRemoteService() = runTest {
        var requestedForceRefresh = false
        val repository = RemoteGroupDirectoryRepository(
            object : GroupDirectoryRemoteService {
                override suspend fun groupDirectory(forceRefresh: Boolean): CastellerGroupDirectory {
                    requestedForceRefresh = forceRefresh
                    return CastellerGroupDirectory(
                        groups = listOf("Colla A"),
                        revision = "test",
                        officialUrl = "https://castellscat.cat/public/ca/les-colles-llistat",
                    )
                }
            },
        )

        val directory = repository.groupDirectory(forceRefresh = true)

        assertEquals(listOf("Colla A"), directory.groups)
        assertTrue(requestedForceRefresh)
    }
}
