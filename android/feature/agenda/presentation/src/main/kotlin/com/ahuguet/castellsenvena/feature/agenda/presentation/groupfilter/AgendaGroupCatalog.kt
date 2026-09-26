package com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter

import com.ahuguet.castellsenvena.core.common.TextFolding
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import com.ahuguet.castellsenvena.core.domain.groups.GroupNameKey
import java.text.Collator
import java.util.Locale

internal object AgendaGroupNameNormalizer {
    fun key(name: String): String = GroupNameKey.normalize(name)

    /**
     * One display name per group key, preferring the first spelling seen, in
     * Catalan alphabetical order ignoring case and accents.
     */
    fun merged(preferred: List<String>, fallback: List<String>): List<String> {
        val namesByKey = LinkedHashMap<String, String>()
        for (name in preferred + fallback) {
            val trimmed = name.trim()
            if (trimmed.isEmpty()) continue
            namesByKey.putIfAbsent(key(trimmed), trimmed)
        }
        val collator = Collator.getInstance(Locale.forLanguageTag("ca-ES")).apply {
            strength = Collator.PRIMARY
        }
        return namesByKey.values.sortedWith(collator::compare)
    }
}

/** Whether a group name matches the search field, ignoring case and accents. */
fun groupMatchesSearch(groupName: String, query: String): Boolean =
    TextFolding.containsIgnoringCaseAndAccents(groupName, query)

/** Every known group: the official directory plus the groups seen in the agenda. */
internal class AgendaGroupCatalog(preferred: List<String>, fallback: List<String> = emptyList()) {
    val names: List<String> = AgendaGroupNameNormalizer.merged(preferred, fallback)
    val keys: Set<String> = names.mapTo(LinkedHashSet(), AgendaGroupNameNormalizer::key)

    fun selectedCount(selection: AgendaGroupSelection): Int = when (selection) {
        AgendaGroupSelection.All -> keys.size
        is AgendaGroupSelection.Custom -> selection.keys.count { it in keys }
    }
}

/** The "other events of the day" start collapsed when some event matches the filter. */
data class AgendaOtherEventsDisclosureState(val isExpanded: Boolean) {
    fun toggled(): AgendaOtherEventsDisclosureState = copy(isExpanded = !isExpanded)

    companion object {
        fun initial(hasMatchingEvents: Boolean) = AgendaOtherEventsDisclosureState(isExpanded = !hasMatchingEvents)
    }
}
