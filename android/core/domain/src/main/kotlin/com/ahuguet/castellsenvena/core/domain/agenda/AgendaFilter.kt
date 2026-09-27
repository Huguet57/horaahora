package com.ahuguet.castellsenvena.core.domain.agenda

/**
 * The groups the user follows in the Agenda. News notifications reuse the
 * same selection, so it lives in the domain instead of the Agenda feature.
 */
sealed interface AgendaGroupSelection {
    /** Every group, including the ones added to the directory in the future. */
    data object All : AgendaGroupSelection

    /** Only these normalized group keys. */
    data class Custom(val keys: Set<String>) : AgendaGroupSelection
}

data class AgendaFilterState(
    val selection: AgendaGroupSelection = AgendaGroupSelection.All,
    val featuredGroupKeys: Set<String> = emptySet(),
    /** Last known group names, so the filter works before the directory loads. */
    val cachedGroups: List<String> = emptyList(),
    val directoryRevision: String? = null,
)

interface AgendaFilterStore {
    fun load(): AgendaFilterState
    fun save(state: AgendaFilterState)
}
