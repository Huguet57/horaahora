package com.ahuguet.castellsenvena.core.data.hourbyhour

import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.database.HourByHourItemRecord
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourPage
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourRepository
import com.ahuguet.castellsenvena.core.network.service.HourByHourRemoteService
import java.time.Instant
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Serves the feed from the network and keeps a copy on the device. When the
 * first page cannot be fetched, the stored copy is shown instead.
 */
class CachedHourByHourRepository(
    private val remoteService: HourByHourRemoteService,
    private val database: CastellsDatabase,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : HourByHourRepository {
    private val queries get() = database.hourByHourItemRecordQueries

    override suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage =
        try {
            val page = remoteService.page(cursor, limit, forceRefresh)
            store(page.items)
            page
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            if (cursor != null) throw failure
            val cached = cachedItems(limit)
            if (cached.isEmpty()) throw failure
            HourByHourPage(items = cached, nextCursor = null, fromCache = true)
        }

    private suspend fun store(items: List<HourByHourItem>) = withContext(ioDispatcher) {
        database.transaction {
            for (item in items) queries.upsert(item.toRecord())
        }
    }

    private suspend fun cachedItems(limit: Int): List<HourByHourItem> = withContext(ioDispatcher) {
        queries.latest(limit.toLong()).executeAsList().map { it.toDomain() }
    }
}

private fun HourByHourItem.toRecord() = HourByHourItemRecord(
    id = id,
    sourceId = sourceId,
    externalId = externalId,
    title = title,
    displayTitle = displayTitle,
    summary = summary,
    publishedAt = publishedAt?.toEpochMilli(),
    sourceOrder = sourceOrder.toLong(),
    articleUrl = articleUrl,
    actionUrl = actionUrl,
    attribution = attribution,
    createdAt = createdAt.toEpochMilli(),
    updatedAt = updatedAt.toEpochMilli(),
)

private fun HourByHourItemRecord.toDomain() = HourByHourItem(
    id = id,
    sourceId = sourceId,
    externalId = externalId,
    title = title,
    displayTitle = displayTitle ?: title,
    summary = summary,
    publishedAt = publishedAt?.let(Instant::ofEpochMilli),
    sourceOrder = sourceOrder.toInt(),
    articleUrl = articleUrl,
    actionUrl = actionUrl,
    attribution = attribution,
    createdAt = Instant.ofEpochMilli(createdAt),
    updatedAt = Instant.ofEpochMilli(updatedAt),
)
