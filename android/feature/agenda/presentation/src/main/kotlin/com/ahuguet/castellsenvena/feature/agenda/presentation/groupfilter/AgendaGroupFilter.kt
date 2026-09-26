package com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterState
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection

/** A snapshot of the group filter for the screens. */
data class AgendaGroupFilterState(
    val availableGroups: List<String> = emptyList(),
    val featuredGroups: List<String> = emptyList(),
    val areAllFeaturedGroupsFollowed: Boolean = false,
    /** False while every group is followed. */
    val isActive: Boolean = false,
    val selectedGroupCount: Int = 0,
    val selection: AgendaGroupSelection = AgendaGroupSelection.All,
    val featuredGroupKeys: Set<String> = emptySet(),
) {
    fun isFollowing(groupName: String): Boolean = when (selection) {
        AgendaGroupSelection.All -> true
        is AgendaGroupSelection.Custom -> AgendaGroupNameNormalizer.key(groupName) in selection.keys
    }

    fun isFeatured(groupName: String): Boolean = AgendaGroupNameNormalizer.key(groupName) in featuredGroupKeys
}

/**
 * The groups the user follows and features. Following every group keeps
 * including groups that appear later; a custom selection does not.
 */
internal class AgendaGroupFilter(private val store: AgendaFilterStore?) {
    var selection: AgendaGroupSelection
        private set
    var featuredGroupKeys: Set<String>
        private set
    var selectedGroupCount: Int
        private set
    private var catalog: AgendaGroupCatalog
    private var directoryRevision: String?

    init {
        val persisted = store?.load() ?: AgendaFilterState()
        catalog = AgendaGroupCatalog(preferred = persisted.cachedGroups)
        selection = persisted.selection
        featuredGroupKeys = persisted.featuredGroupKeys
        selectedGroupCount = catalog.selectedCount(persisted.selection)
        directoryRevision = persisted.directoryRevision
    }

    val availableGroups: List<String> get() = catalog.names

    val featuredGroups: List<String> get() = availableGroups.filter { key(it) in featuredGroupKeys }

    val areAllFeaturedGroupsFollowed: Boolean
        get() = featuredGroups.let { featured -> featured.isNotEmpty() && featured.all(::isFollowing) }

    val isActive: Boolean get() = selection is AgendaGroupSelection.Custom

    fun snapshot() = AgendaGroupFilterState(
        availableGroups = availableGroups,
        featuredGroups = featuredGroups,
        areAllFeaturedGroupsFollowed = areAllFeaturedGroupsFollowed,
        isActive = isActive,
        selectedGroupCount = selectedGroupCount,
        selection = selection,
        featuredGroupKeys = featuredGroupKeys,
    )

    fun isFollowing(groupName: String): Boolean = when (val current = selection) {
        AgendaGroupSelection.All -> true
        is AgendaGroupSelection.Custom -> key(groupName) in current.keys
    }

    fun isFeatured(groupName: String): Boolean = key(groupName) in featuredGroupKeys

    fun matches(participatingGroupKeys: Set<String>): Boolean = when (val current = selection) {
        AgendaGroupSelection.All -> true
        is AgendaGroupSelection.Custom -> current.keys.any { it in participatingGroupKeys }
    }

    fun setFollowing(following: Boolean, groupName: String) {
        val groupKey = key(groupName)
        selection = when (val current = selection) {
            AgendaGroupSelection.All -> {
                if (following) return
                AgendaGroupSelection.Custom(catalog.keys - groupKey)
            }
            is AgendaGroupSelection.Custom ->
                AgendaGroupSelection.Custom(if (following) current.keys + groupKey else current.keys - groupKey)
        }
        selectionChanged()
    }

    fun followAll() {
        if (!isActive) return
        selection = AgendaGroupSelection.All
        selectionChanged()
    }

    fun toggleFollowingAll() {
        selection = if (isActive) AgendaGroupSelection.All else AgendaGroupSelection.Custom(emptySet())
        selectionChanged()
    }

    fun toggleFollowingFeatured() {
        val featuredKeys = featuredGroups.mapTo(HashSet(), ::key)
        if (featuredKeys.isEmpty()) return
        selection = when (val current = selection) {
            AgendaGroupSelection.All -> AgendaGroupSelection.Custom(catalog.keys - featuredKeys)
            is AgendaGroupSelection.Custom -> AgendaGroupSelection.Custom(
                if (areAllFeaturedGroupsFollowed) current.keys - featuredKeys else current.keys + featuredKeys,
            )
        }
        selectionChanged()
    }

    fun setFeatured(featured: Boolean, groupName: String) {
        val groupKey = key(groupName)
        featuredGroupKeys = if (featured) featuredGroupKeys + groupKey else featuredGroupKeys - groupKey
        persist()
    }

    fun mergeDirectory(groups: List<String>, revision: String, observedGroups: List<String>) {
        catalog = AgendaGroupCatalog(preferred = groups, fallback = catalog.names + observedGroups)
        selectedGroupCount = catalog.selectedCount(selection)
        if (revision.isNotEmpty()) directoryRevision = revision
        persist()
    }

    fun mergeObservedGroups(groups: List<String>) {
        catalog = AgendaGroupCatalog(preferred = catalog.names, fallback = groups)
        selectedGroupCount = catalog.selectedCount(selection)
        persist()
    }

    private fun selectionChanged() {
        selectedGroupCount = catalog.selectedCount(selection)
        persist()
    }

    private fun key(groupName: String): String = AgendaGroupNameNormalizer.key(groupName)

    private fun persist() {
        store?.save(
            AgendaFilterState(
                selection = selection,
                featuredGroupKeys = featuredGroupKeys,
                cachedGroups = catalog.names,
                directoryRevision = directoryRevision,
            ),
        )
    }
}
