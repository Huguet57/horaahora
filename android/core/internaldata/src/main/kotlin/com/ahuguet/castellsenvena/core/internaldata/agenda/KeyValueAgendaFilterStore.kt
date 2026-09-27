package com.ahuguet.castellsenvena.core.internaldata.agenda

import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterState
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json

/**
 * Persists the Agenda group filter. [onSelectionChange] only fires when the
 * followed groups change, not when the featured groups or the directory do.
 */
class KeyValueAgendaFilterStore(
    private val store: KeyValueStore,
    private val key: String = DEFAULT_KEY,
) : AgendaFilterStore {
    var onSelectionChange: ((AgendaGroupSelection) -> Unit)? = null

    override fun load(): AgendaFilterState {
        val stored = store.getString(key) ?: return AgendaFilterState()
        return try {
            json.decodeFromString(StoredAgendaFilterState.serializer(), stored).toDomain()
        } catch (_: SerializationException) {
            AgendaFilterState()
        } catch (_: IllegalArgumentException) {
            AgendaFilterState()
        }
    }

    override fun save(state: AgendaFilterState) {
        val previousSelection = load().selection
        store.putString(key, json.encodeToString(StoredAgendaFilterState.serializer(), StoredAgendaFilterState(state)))
        if (previousSelection != state.selection) onSelectionChange?.invoke(state.selection)
    }

    companion object {
        const val DEFAULT_KEY = "castells.agenda.group-filter.v1"
        private val json = Json { ignoreUnknownKeys = true }
    }
}

@Serializable
private data class StoredAgendaFilterState(
    val selection: StoredSelection = StoredSelection(),
    val featuredGroupKeys: List<String> = emptyList(),
    val cachedGroups: List<String> = emptyList(),
    val directoryRevision: String? = null,
) {
    constructor(state: AgendaFilterState) : this(
        selection = when (val selection = state.selection) {
            AgendaGroupSelection.All -> StoredSelection()
            is AgendaGroupSelection.Custom -> StoredSelection(mode = CUSTOM, keys = selection.keys.sorted())
        },
        featuredGroupKeys = state.featuredGroupKeys.sorted(),
        cachedGroups = state.cachedGroups,
        directoryRevision = state.directoryRevision,
    )

    fun toDomain() = AgendaFilterState(
        selection = if (selection.mode == CUSTOM) {
            AgendaGroupSelection.Custom(selection.keys.toSet())
        } else {
            AgendaGroupSelection.All
        },
        featuredGroupKeys = featuredGroupKeys.toSet(),
        cachedGroups = cachedGroups,
        directoryRevision = directoryRevision,
    )
}

@Serializable
private data class StoredSelection(
    val mode: String = ALL,
    val keys: List<String> = emptyList(),
)

private const val ALL = "all"
private const val CUSTOM = "custom"
