package com.ahuguet.castellsenvena.core.domain.hourbyhour

import java.time.Instant

data class HourByHourItem(
    val id: String,
    val sourceId: String,
    val externalId: String,
    val title: String,
    val displayTitle: String,
    val summary: String,
    val publishedAt: Instant?,
    val sourceOrder: Int,
    val articleUrl: String,
    val actionUrl: String?,
    val attribution: String,
    val createdAt: Instant,
    val updatedAt: Instant,
) {
    /**
     * The link the item opens, or null when it is read inside the app. Older
     * Revista Castells entries used the article URL as a fallback.
     */
    val associatedUrl: String?
        get() = if (sourceId == REVISTA_CASTELLS && actionUrl == articleUrl) null else actionUrl

    companion object {
        const val REVISTA_CASTELLS = "revista-castells"
    }
}

data class HourByHourPage(
    val items: List<HourByHourItem>,
    val nextCursor: String?,
    val fromCache: Boolean,
)

interface HourByHourRepository {
    suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage
}
