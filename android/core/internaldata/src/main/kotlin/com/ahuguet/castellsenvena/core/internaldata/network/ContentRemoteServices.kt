package com.ahuguet.castellsenvena.core.internaldata.network

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.groups.CastellerGroupDirectory
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourPage
import com.ahuguet.castellsenvena.core.network.ApiClient
import java.time.LocalDate

interface HourByHourRemoteService {
    suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage
}

class HttpHourByHourRemoteService(private val client: ApiClient) : HourByHourRemoteService {
    override suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage {
        val query = buildList {
            add("limit" to limit.toString())
            if (cursor != null) add("cursor" to cursor)
            if (forceRefresh) add("refresh" to "true")
        }
        return client.get("/v1/hour-by-hour", query, HourByHourPageDto.serializer()).toDomain()
    }
}

interface AgendaRemoteService {
    suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage
}

class HttpAgendaRemoteService(private val client: ApiClient) : AgendaRemoteService {
    override suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage {
        // Agenda days are Europe/Madrid calendar dates, sent as yyyy-MM-dd.
        val query = buildList {
            add("from" to from.toString())
            add("to" to to.toString())
            add("limit" to limit.toString())
            if (!group.isNullOrEmpty()) add("group" to group)
            if (!municipality.isNullOrEmpty()) add("municipality" to municipality)
            if (cursor != null) add("cursor" to cursor)
            if (forceRefresh) add("refresh" to "true")
        }
        return client.get("/v1/events", query, AgendaPageDto.serializer()).toDomain()
    }
}

interface GroupDirectoryRemoteService {
    suspend fun groupDirectory(forceRefresh: Boolean): CastellerGroupDirectory
}

class HttpGroupDirectoryRemoteService(private val client: ApiClient) : GroupDirectoryRemoteService {
    override suspend fun groupDirectory(forceRefresh: Boolean): CastellerGroupDirectory {
        val query = if (forceRefresh) listOf("refresh" to "true") else emptyList()
        return client.get("/v1/groups", query, CastellerGroupDirectoryDto.serializer()).toDomain()
    }
}
