package com.ahuguet.castellsenvena.core.domain.agenda

import java.time.Instant
import java.time.LocalDate

data class CastellEvent(
    val id: String,
    val sourceId: String,
    val externalId: String,
    val title: String,
    /** The day of the event in the Europe/Madrid calendar, as `yyyy-MM-dd`. */
    val localDate: String,
    val startsAt: Instant?,
    /** Either an exact time ("18:00") or an imprecise one ("Tarda"). */
    val timeLabel: String,
    val timezone: String,
    val venue: String,
    val municipality: String,
    val participatingGroups: List<String>,
    val notes: String,
    val sourceUrl: String,
    val sourceOrder: Int,
    val attribution: String,
    val revision: String,
    val updatedAt: Instant,
)

enum class AgendaSourceStatus {
    ACTIVE,
    UNAVAILABLE,
}

data class AgendaPage(
    val items: List<CastellEvent>,
    val nextCursor: String?,
    val officialUrl: String,
    val fromCache: Boolean,
    val sourceStatus: AgendaSourceStatus,
)

interface AgendaRepository {
    val officialUrl: String

    /** Events already stored on the device, without contacting the server. */
    suspend fun cachedEvents(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
    ): List<CastellEvent> = emptyList()

    suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage

    companion object {
        const val OFFICIAL_AGENDA_URL = "https://castellscat.cat/ca/agenda"
    }
}
