package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem

internal object HourByHourItemMerger {
    enum class Policy {
        /** A pull to refresh: the fresh first page replaces the list. */
        REPLACE,

        /** Pagination: older items go after the loaded ones. */
        APPEND,

        /** A background check: known items are updated and paginated ones stay. */
        REVALIDATE,
    }

    data class Result(val items: List<HourByHourItem>, val containsNewItems: Boolean)

    fun merge(incoming: List<HourByHourItem>, existing: List<HourByHourItem>, policy: Policy): Result {
        val existingIdentities = existing.mapTo(HashSet(), ::Identity)
        val containsNewItems = policy == Policy.REVALIDATE &&
            existing.isNotEmpty() &&
            incoming.any { Identity(it) !in existingIdentities }

        val candidates = when (policy) {
            Policy.REPLACE -> incoming
            Policy.APPEND -> existing + incoming
            Policy.REVALIDATE -> incoming + existing
        }
        val seen = HashSet<Identity>()
        return Result(items = candidates.filter { seen.add(Identity(it)) }, containsNewItems = containsNewItems)
    }

    /** An item is the same article when both its source and its external id match. */
    private data class Identity(val sourceId: String, val externalId: String) {
        constructor(item: HourByHourItem) : this(item.sourceId, item.externalId)
    }
}
