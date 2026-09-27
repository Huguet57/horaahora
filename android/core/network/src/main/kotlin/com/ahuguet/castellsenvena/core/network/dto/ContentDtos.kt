@file:UseSerializers(FlexibleInstantSerializer::class)

package com.ahuguet.castellsenvena.core.network.dto

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.core.domain.groups.CastellerGroupDirectory
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourPage
import com.ahuguet.castellsenvena.core.network.FlexibleInstantSerializer
import java.time.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers

@Serializable
internal data class HourByHourItemDto(
    val id: String,
    @SerialName("source_id") val sourceId: String,
    @SerialName("external_id") val externalId: String,
    val title: String,
    @SerialName("display_title") val displayTitle: String? = null,
    val summary: String,
    @SerialName("published_at") val publishedAt: Instant? = null,
    @SerialName("source_order") val sourceOrder: Int,
    @SerialName("article_url") val articleUrl: String,
    @SerialName("action_url") val actionUrl: String? = null,
    val attribution: String,
    @SerialName("created_at") val createdAt: Instant,
    @SerialName("updated_at") val updatedAt: Instant,
) {
    fun toDomain() = HourByHourItem(
        id = id,
        sourceId = sourceId,
        externalId = externalId,
        title = title,
        displayTitle = displayTitle ?: title,
        summary = summary,
        publishedAt = publishedAt,
        sourceOrder = sourceOrder,
        articleUrl = articleUrl,
        actionUrl = actionUrl,
        attribution = attribution,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )
}

@Serializable
internal data class HourByHourPageDto(
    val items: List<HourByHourItemDto>,
    @SerialName("next_cursor") val nextCursor: String? = null,
    @SerialName("from_cache") val fromCache: Boolean,
) {
    fun toDomain() = HourByHourPage(
        items = items.map(HourByHourItemDto::toDomain),
        nextCursor = nextCursor,
        fromCache = fromCache,
    )
}

@Serializable
internal data class CastellEventDto(
    val id: String,
    @SerialName("source_id") val sourceId: String,
    @SerialName("external_id") val externalId: String,
    val title: String,
    @SerialName("local_date") val localDate: String,
    @SerialName("starts_at") val startsAt: Instant? = null,
    @SerialName("time_label") val timeLabel: String,
    val timezone: String,
    val venue: String,
    val municipality: String,
    @SerialName("participating_groups") val participatingGroups: List<String>,
    val notes: String,
    @SerialName("source_url") val sourceUrl: String,
    @SerialName("source_order") val sourceOrder: Int,
    val attribution: String,
    val revision: String,
    @SerialName("updated_at") val updatedAt: Instant,
) {
    fun toDomain() = CastellEvent(
        id = id,
        sourceId = sourceId,
        externalId = externalId,
        title = title,
        localDate = localDate,
        startsAt = startsAt,
        timeLabel = timeLabel,
        timezone = timezone,
        venue = venue,
        municipality = municipality,
        participatingGroups = participatingGroups,
        notes = notes,
        sourceUrl = sourceUrl,
        sourceOrder = sourceOrder,
        attribution = attribution,
        revision = revision,
        updatedAt = updatedAt,
    )
}

@Serializable
internal enum class AgendaSourceStatusDto(val status: AgendaSourceStatus) {
    @SerialName("active")
    ACTIVE(AgendaSourceStatus.ACTIVE),

    @SerialName("unavailable")
    UNAVAILABLE(AgendaSourceStatus.UNAVAILABLE),
}

@Serializable
internal data class AgendaPageDto(
    val items: List<CastellEventDto>,
    @SerialName("next_cursor") val nextCursor: String? = null,
    @SerialName("official_url") val officialUrl: String = AgendaRepository.OFFICIAL_AGENDA_URL,
    @SerialName("from_cache") val fromCache: Boolean,
    @SerialName("source_status") val sourceStatus: AgendaSourceStatusDto,
) {
    fun toDomain() = AgendaPage(
        items = items.map(CastellEventDto::toDomain),
        nextCursor = nextCursor,
        officialUrl = officialUrl,
        fromCache = fromCache,
        sourceStatus = sourceStatus.status,
    )
}

@Serializable
internal data class CastellerGroupDirectoryDto(
    val groups: List<String>,
    val revision: String,
    @SerialName("official_url") val officialUrl: String,
) {
    fun toDomain() = CastellerGroupDirectory(
        groups = groups,
        revision = revision,
        officialUrl = officialUrl,
    )
}
