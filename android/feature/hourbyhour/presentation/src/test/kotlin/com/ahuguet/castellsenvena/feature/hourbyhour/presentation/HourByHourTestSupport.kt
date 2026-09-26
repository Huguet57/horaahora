package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourPage
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourRepository
import java.time.Instant
import kotlin.time.Duration
import kotlinx.coroutines.CompletableDeferred

val defaultTimestamp: Instant = Instant.ofEpochSecond(1_700_000_000)

fun page(items: List<HourByHourItem>, nextCursor: String? = null) =
    HourByHourPage(items = items, nextCursor = nextCursor, fromCache = false)

fun item(
    id: String,
    title: String? = null,
    publishedAt: Instant? = null,
    sourceId: String = "revista-castells",
    externalId: String? = null,
): HourByHourItem {
    val timestamp = publishedAt ?: defaultTimestamp
    return HourByHourItem(
        id = id,
        sourceId = sourceId,
        externalId = externalId ?: id,
        title = title ?: id,
        displayTitle = title ?: id,
        summary = "",
        publishedAt = timestamp,
        sourceOrder = 0,
        articleUrl = "https://example.com/$id",
        actionUrl = null,
        attribution = "Revista Castells",
        createdAt = timestamp,
        updatedAt = timestamp,
    )
}

class MissingPageException : Exception("No page left")

class SequencedHourByHourRepository(pages: List<HourByHourPage>) : HourByHourRepository {
    data class Request(val cursor: String?, val forceRefresh: Boolean)

    private val pages = ArrayDeque(pages)
    val requests = mutableListOf<Request>()

    override suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage {
        requests += Request(cursor, forceRefresh)
        return pages.removeFirstOrNull() ?: throw MissingPageException()
    }
}

class SuspendingHourByHourRepository(private val result: HourByHourPage) : HourByHourRepository {
    val requests = mutableListOf<Boolean>()
    private val released = CompletableDeferred<Unit>()

    override suspend fun page(cursor: String?, limit: Int, forceRefresh: Boolean): HourByHourPage {
        requests += forceRefresh
        released.await()
        return result
    }

    fun resume() {
        released.complete(Unit)
    }
}

/** Lets a fixed number of sleeps succeed, then fails like a cancelled sleep. */
class SequencedSleeper(private var successfulSleeps: Int) {
    val durations = mutableListOf<Duration>()

    suspend fun sleep(duration: Duration) {
        durations += duration
        if (successfulSleeps <= 0) throw kotlin.coroutines.cancellation.CancellationException("Stopped")
        successfulSleeps -= 1
    }
}
