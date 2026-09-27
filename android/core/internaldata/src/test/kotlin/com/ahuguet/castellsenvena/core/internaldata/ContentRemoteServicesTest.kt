package com.ahuguet.castellsenvena.core.internaldata

import com.ahuguet.castellsenvena.core.internaldata.network.HttpAgendaRemoteService
import com.ahuguet.castellsenvena.core.internaldata.network.HttpGroupDirectoryRemoteService
import com.ahuguet.castellsenvena.core.internaldata.network.HttpHourByHourRemoteService
import com.ahuguet.castellsenvena.core.network.ApiClient
import java.time.LocalDate
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer

/** The requests of the Hora a Hora, Agenda and group directory endpoints. */
class ContentRemoteServicesTest {
    private val server = MockWebServer()
    private lateinit var client: ApiClient

    @BeforeTest
    fun setUp() {
        server.start()
        client = ApiClient(server.url("/service/").toString())
    }

    @AfterTest
    fun tearDown() {
        server.close()
    }

    @Test
    fun agendaRequestSendsTheMadridDatesAndOptionalFilters() = runTest {
        server.enqueue(MockResponse(body = EMPTY_AGENDA))

        HttpAgendaRemoteService(client).events(
            from = LocalDate.of(2026, 1, 1),
            to = LocalDate.of(2026, 7, 31),
            group = "Colla Vella",
            municipality = "",
            cursor = "next page",
            limit = 100,
            forceRefresh = true,
        )

        val url = server.takeRequest().url
        assertEquals("/service/v1/events", url.encodedPath)
        assertEquals("2026-01-01", url.queryParameter("from"))
        assertEquals("2026-07-31", url.queryParameter("to"))
        assertEquals("100", url.queryParameter("limit"))
        assertEquals("Colla Vella", url.queryParameter("group"))
        assertEquals(null, url.queryParameter("municipality"))
        assertEquals("next page", url.queryParameter("cursor"))
        assertEquals("true", url.queryParameter("refresh"))
    }

    @Test
    fun hourByHourAndGroupsOnlyForceTheSourceWhenAsked() = runTest {
        server.enqueue(MockResponse(body = """{"items":[],"next_cursor":null,"from_cache":false}"""))
        server.enqueue(MockResponse(body = """{"groups":["A"],"revision":"r","official_url":"https://x"}"""))

        HttpHourByHourRemoteService(client).page(cursor = null, limit = 30, forceRefresh = false)
        val directory = HttpGroupDirectoryRemoteService(client).groupDirectory(forceRefresh = true)

        val hourByHour = server.takeRequest().url
        assertEquals("/service/v1/hour-by-hour", hourByHour.encodedPath)
        assertEquals("30", hourByHour.queryParameter("limit"))
        assertEquals(null, hourByHour.queryParameter("refresh"))
        assertEquals("true", server.takeRequest().url.queryParameter("refresh"))
        assertEquals(listOf("A"), directory.groups)
    }

    private companion object {
        const val EMPTY_AGENDA =
            """{"items":[],"next_cursor":null,"official_url":"https://castellscat.cat/ca/agenda","from_cache":false,"source_status":"active"}"""
    }
}
