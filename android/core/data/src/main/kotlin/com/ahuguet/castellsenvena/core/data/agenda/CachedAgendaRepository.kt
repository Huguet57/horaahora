package com.ahuguet.castellsenvena.core.data.agenda

import com.ahuguet.castellsenvena.core.common.TextFolding
import com.ahuguet.castellsenvena.core.database.AgendaEventRecord
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.core.network.service.AgendaRemoteService
import java.time.Instant
import java.time.LocalDate
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json

/**
 * Serves the agenda from the network and keeps the loaded days on the device,
 * so they can be read offline or while the official source is unavailable.
 */
class CachedAgendaRepository(
    private val remoteService: AgendaRemoteService,
    private val database: CastellsDatabase,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : AgendaRepository {
    override val officialUrl: String = AgendaRepository.OFFICIAL_AGENDA_URL

    private val queries get() = database.agendaEventRecordQueries

    override suspend fun cachedEvents(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
    ): List<CastellEvent> = cachedItems(from, to, group, municipality, limit = Int.MAX_VALUE)

    override suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage =
        try {
            val page = remoteService.events(from, to, group, municipality, cursor, limit, forceRefresh)
            if (page.sourceStatus == AgendaSourceStatus.UNAVAILABLE) purgeDemoItems()
            store(
                items = page.items,
                from = from,
                to = to,
                replacingCompleteRange = cursor == null &&
                    page.nextCursor == null &&
                    group == null &&
                    municipality == null &&
                    page.sourceStatus == AgendaSourceStatus.ACTIVE,
            )
            val cached = if (page.items.isEmpty() &&
                page.sourceStatus == AgendaSourceStatus.UNAVAILABLE &&
                cursor == null
            ) {
                cachedItems(from, to, group, municipality, limit)
            } else {
                emptyList()
            }
            if (cached.isNotEmpty()) {
                AgendaPage(
                    items = cached,
                    nextCursor = null,
                    officialUrl = page.officialUrl,
                    fromCache = true,
                    sourceStatus = AgendaSourceStatus.UNAVAILABLE,
                )
            } else {
                page
            }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            if (cursor != null) throw failure
            val cached = cachedItems(from, to, group, municipality, limit)
            if (cached.isEmpty()) throw failure
            AgendaPage(
                items = cached,
                nextCursor = null,
                officialUrl = officialUrl,
                fromCache = true,
                sourceStatus = AgendaSourceStatus.ACTIVE,
            )
        }

    /**
     * A complete, unfiltered answer replaces the stored range, so cancelled
     * events disappear from the offline copy too.
     */
    private suspend fun store(
        items: List<CastellEvent>,
        from: LocalDate,
        to: LocalDate,
        replacingCompleteRange: Boolean,
    ) = withContext(ioDispatcher) {
        database.transaction {
            val stale = if (replacingCompleteRange) {
                val incomingIds = items.mapTo(HashSet()) { it.id }
                queries.inRange(from.toString(), to.toString()).executeAsList()
                    .filter { it.id !in incomingIds }
            } else {
                emptyList()
            }
            for (item in items) queries.upsert(item.toRecord())
            for (record in stale) queries.deleteById(record.id)
        }
    }

    private suspend fun cachedItems(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        limit: Int,
    ): List<CastellEvent> = withContext(ioDispatcher) {
        val groupKey = group?.let(::searchKey)
        val municipalityKey = municipality?.let(::searchKey)
        queries.inRange(from.toString(), to.toString()).executeAsList()
            .asSequence()
            .filterNot(::isDemo)
            .map { it.toDomain() }
            .filter { event ->
                (groupKey == null || event.participatingGroups.any { searchKey(it) == groupKey }) &&
                    (municipalityKey == null || searchKey(event.municipality) == municipalityKey)
            }
            .take(limit)
            .toList()
    }

    private suspend fun purgeDemoItems() = withContext(ioDispatcher) {
        database.transaction {
            for (record in queries.all().executeAsList().filter(::isDemo)) {
                queries.deleteById(record.id)
            }
        }
    }

    private companion object {
        val groupsSerializer = ListSerializer(String.serializer())

        /** Simulated local data must never be shown as the official agenda. */
        fun isDemo(record: AgendaEventRecord): Boolean =
            record.sourceId == "cccc-fixture" ||
                record.title.contains("demostració", ignoreCase = true) ||
                record.notes.contains("dada simulada", ignoreCase = true)

        fun searchKey(value: String): String = TextFolding.collapseWhitespace(TextFolding.fold(value))

        fun CastellEvent.toRecord() = AgendaEventRecord(
            id = id,
            sourceId = sourceId,
            externalId = externalId,
            title = title,
            localDate = localDate,
            startsAt = startsAt?.toEpochMilli(),
            timeLabel = timeLabel,
            timezone = timezone,
            venue = venue,
            municipality = municipality,
            participatingGroups = Json.encodeToString(groupsSerializer, participatingGroups),
            notes = notes,
            sourceUrl = sourceUrl,
            sourceOrder = sourceOrder.toLong(),
            attribution = attribution,
            revision = revision,
            updatedAt = updatedAt.toEpochMilli(),
        )

        fun AgendaEventRecord.toDomain() = CastellEvent(
            id = id,
            sourceId = sourceId,
            externalId = externalId,
            title = title,
            localDate = localDate,
            startsAt = startsAt?.let(Instant::ofEpochMilli),
            timeLabel = timeLabel,
            timezone = timezone,
            venue = venue,
            municipality = municipality,
            participatingGroups = runCatching {
                Json.decodeFromString(groupsSerializer, participatingGroups)
            }.getOrDefault(emptyList()),
            notes = notes,
            sourceUrl = sourceUrl,
            sourceOrder = sourceOrder.toInt(),
            attribution = attribution,
            revision = revision,
            updatedAt = Instant.ofEpochMilli(updatedAt),
        )
    }
}
