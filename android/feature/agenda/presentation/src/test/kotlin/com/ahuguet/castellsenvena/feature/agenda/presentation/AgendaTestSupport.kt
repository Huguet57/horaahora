package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterState
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaFilterStore
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaRepository
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.core.domain.groups.CastellerGroupDirectory
import com.ahuguet.castellsenvena.core.domain.groups.GroupDirectoryRepository
import java.io.IOException
import java.time.Instant
import java.time.LocalDate
import kotlinx.coroutines.CompletableDeferred

const val OFFICIAL_URL = "https://castellscat.cat/ca/agenda"

fun agendaDate(localDate: String): LocalDate = LocalDate.parse(localDate)

fun makeAgendaEvent(
    id: String,
    localDate: String,
    title: String,
    municipality: String = "Valls",
    sourceOrder: Int = 0,
    participatingGroups: List<String> = listOf("Colla A"),
) = CastellEvent(
    id = id,
    sourceId = "cccc",
    externalId = id,
    title = title,
    localDate = localDate,
    startsAt = null,
    timeLabel = "Matí",
    timezone = "Europe/Madrid",
    venue = "Plaça",
    municipality = municipality,
    participatingGroups = participatingGroups,
    notes = "",
    sourceUrl = OFFICIAL_URL,
    sourceOrder = sourceOrder,
    attribution = "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
    revision = "r1",
    updatedAt = Instant.parse("2026-07-21T10:00:00Z"),
)

class AgendaRepositoryStub(
    private var suppliedItems: List<CastellEvent>? = null,
    private val suppliedCachedItems: List<CastellEvent> = emptyList(),
    private val remoteError: Exception? = null,
) : AgendaRepository {
    data class Request(val from: String, val to: String, val forceRefresh: Boolean)

    override val officialUrl: String = OFFICIAL_URL
    var requestedLimit: Int? = null
    val requests = mutableListOf<Request>()
    val cachedRequests = mutableListOf<Pair<String, String>>()
    private var shouldSuspendNextRequest = false
    private var onlySuspendForcedRefresh = false
    private var suspendedRequest: CompletableDeferred<Unit>? = null

    val hasSuspendedRequest: Boolean get() = suspendedRequest != null

    fun suspendNextRequest() {
        shouldSuspendNextRequest = true
        onlySuspendForcedRefresh = false
    }

    fun suspendNextForcedRefresh() {
        shouldSuspendNextRequest = true
        onlySuspendForcedRefresh = true
    }

    fun resumeSuspendedRequest(items: List<CastellEvent>? = null) {
        if (items != null) suppliedItems = items
        val request = suspendedRequest
        suspendedRequest = null
        request?.complete(Unit)
    }

    override suspend fun cachedEvents(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
    ): List<CastellEvent> {
        val lower = from.toString()
        val upper = to.toString()
        cachedRequests += lower to upper
        return suppliedCachedItems.filter { it.localDate in lower..upper }
    }

    override suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage {
        remoteError?.let { throw it }
        requestedLimit = limit
        val lower = from.toString()
        val upper = to.toString()
        requests += Request(lower, upper, forceRefresh)
        if (shouldSuspendNextRequest && (!onlySuspendForcedRefresh || forceRefresh)) {
            shouldSuspendNextRequest = false
            val suspension = CompletableDeferred<Unit>()
            suspendedRequest = suspension
            suspension.await()
        }
        val availableItems = suppliedItems ?: listOf(
            makeAgendaEvent(id = "1", localDate = "2026-07-21", title = "Diada nativa"),
            makeAgendaEvent(
                id = "2",
                localDate = "2026-07-22",
                title = "Diada següent",
                municipality = "Tarragona",
                sourceOrder = 1,
            ),
        )
        return AgendaPage(
            items = availableItems.filter { it.localDate in lower..upper },
            nextCursor = null,
            officialUrl = OFFICIAL_URL,
            fromCache = false,
            sourceStatus = AgendaSourceStatus.ACTIVE,
        )
    }
}

object AgendaGroupFilterFixture {
    val day: LocalDate = LocalDate.of(2026, 7, 25)

    fun event(id: String, groups: List<String>) =
        makeAgendaEvent(id = id, localDate = "2026-07-25", title = id, participatingGroups = groups)
}

/** Serves the same events for every range, plus a directory of groups. */
class GroupAgendaRepositoryStub(
    private val suppliedItems: List<CastellEvent>,
    var directoryGroups: List<String>,
) : AgendaRepository, GroupDirectoryRepository {
    override val officialUrl: String = OFFICIAL_URL
    var eventRequestCount = 0

    override suspend fun events(
        from: LocalDate,
        to: LocalDate,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Boolean,
    ): AgendaPage {
        eventRequestCount += 1
        return AgendaPage(
            items = suppliedItems,
            nextCursor = null,
            officialUrl = OFFICIAL_URL,
            fromCache = false,
            sourceStatus = AgendaSourceStatus.ACTIVE,
        )
    }

    override suspend fun groupDirectory(forceRefresh: Boolean) = CastellerGroupDirectory(
        groups = directoryGroups,
        revision = "test",
        officialUrl = "https://castellscat.cat/public/ca/les-colles-llistat",
    )

    fun makeModel(filterStore: AgendaFilterStore? = null) = AgendaViewModel(
        repository = this,
        groupDirectoryRepository = this,
        filterStore = filterStore,
    )
}

class GroupDirectoryRepositoryStub(private val groups: List<String>) : GroupDirectoryRepository {
    override suspend fun groupDirectory(forceRefresh: Boolean) = CastellerGroupDirectory(
        groups = groups,
        revision = "dedicated-test",
        officialUrl = "https://castellscat.cat/public/ca/les-colles-llistat",
    )
}

class InMemoryAgendaFilterStore : AgendaFilterStore {
    private var state = AgendaFilterState()

    override fun load(): AgendaFilterState = state

    override fun save(state: AgendaFilterState) {
        this.state = state
    }
}

fun offline() = IOException("The Internet connection appears to be offline.")
