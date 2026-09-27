package com.ahuguet.castellsenvena.core.network

import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequestMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.network.service.HttpAgendaRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpChatRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpGroupDirectoryRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpHourByHourRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpPushSubscriptionRemoteService
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRequest
import java.time.LocalDate
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer

class ApiClientTest {
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

    @Test
    fun httpErrorsExposeTheServerDetail() = runTest {
        server.enqueue(MockResponse(code = 429, body = """{"detail":"Massa consultes. Torna-ho a provar."}"""))

        val failure = assertFailsWith<ApiException.Http> {
            HttpHourByHourRemoteService(client).page(cursor = null, limit = 30, forceRefresh = false)
        }

        assertEquals(429, failure.statusCode)
        assertEquals("Massa consultes. Torna-ho a provar.", failure.userMessage)
    }

    @Test
    fun validationErrorsWithoutATextDetailUseTheStatusMessage() = runTest {
        server.enqueue(MockResponse(code = 422, body = """{"detail":[{"msg":"invalid"}]}"""))

        val failure = assertFailsWith<ApiException.Http> {
            HttpHourByHourRemoteService(client).page(cursor = null, limit = 30, forceRefresh = false)
        }

        assertEquals("El servidor ha retornat l'error 422.", failure.userMessage)
    }

    @Test
    fun malformedResponsesAreReportedAsInvalid() = runTest {
        server.enqueue(MockResponse(body = """{"items": "not a list"}"""))

        val failure = assertFailsWith<ApiException.InvalidResponse> {
            HttpHourByHourRemoteService(client).page(cursor = null, limit = 30, forceRefresh = false)
        }

        assertEquals("La resposta del servidor no és vàlida.", failure.userMessage)
    }

    @Test
    fun unreachableServersAreReportedAsNetworkFailures() = runTest {
        val url = server.url("/").toString()
        server.close()

        val failure = assertFailsWith<ApiException.Network> {
            HttpHourByHourRemoteService(ApiClient(url)).page(cursor = null, limit = 30, forceRefresh = false)
        }

        assertTrue(failure.userMessage.startsWith("No s'ha pogut connectar"))
    }

    @Test
    fun chatSendsOnlyTheLatestTwelveMessagesInSnakeCase() = runTest {
        server.enqueue(
            MockResponse(
                body = """{"reply":"R","intent":"total","performances":[],"winner_label":null,
                    "warnings":[],"ruleset_version":"concurs-2026","needs_clarification":false}""",
            ),
        )
        val messages = (1..14).map { ChatRequestMessage(ChatRole.USER, "missatge $it") }

        val response = HttpChatRemoteService(client).send(
            ChatRequest(conversationId = "conversation", installationId = "installation", messages = messages),
        )

        val request = server.takeRequest()
        val body = Json.parseToJsonElement(request.body!!.utf8()).jsonObject
        assertEquals("POST", request.method)
        assertEquals("/service/v1/chat", request.url.encodedPath)
        assertEquals("conversation", body.getValue("conversation_id").jsonPrimitive.content)
        assertEquals("installation", body.getValue("installation_id").jsonPrimitive.content)
        assertEquals("ca-ES", body.getValue("locale").jsonPrimitive.content)
        assertEquals("concurs-2026", body.getValue("ruleset").jsonPrimitive.content)
        val sent = body.getValue("messages").jsonArray
        assertEquals(12, sent.size)
        assertEquals("missatge 3", sent.first().jsonObject.getValue("content").jsonPrimitive.content)
        assertEquals("user", sent.first().jsonObject.getValue("role").jsonPrimitive.content)
        assertEquals("R", response.reply)
    }

    @Test
    fun chatShortensStoredMessagesToTheLengthTheBackendAccepts() = runTest {
        server.enqueue(
            MockResponse(
                body = """{"reply":"R","intent":"total","performances":[],"winner_label":null,
                    "warnings":[],"ruleset_version":"concurs-2026","needs_clarification":false}""",
            ),
        )
        val oversized = ChatRequestMessage(ChatRole.USER, "a".repeat(ChatRequest.MAX_MESSAGE_LENGTH + 50))

        HttpChatRemoteService(client).send(
            ChatRequest(conversationId = "conversation", installationId = "installation", messages = listOf(oversized)),
        )

        val body = Json.parseToJsonElement(server.takeRequest().body!!.utf8()).jsonObject
        val content = body.getValue("messages").jsonArray.single().jsonObject.getValue("content").jsonPrimitive.content
        assertEquals(ChatRequest.MAX_MESSAGE_LENGTH, content.length)
    }

    @Test
    fun pushRegistrationSendsTheAppTheAndroidTokenAndPreferences() = runTest {
        server.enqueue(MockResponse(code = 204))
        server.enqueue(MockResponse(code = 204))
        // The internal app is a separate app, and the backend keeps its subscriptions apart.
        val service = HttpPushSubscriptionRemoteService(client, appId = "com.ahuguet.castellsenvena.internal")

        service.register(
            PushSubscriptionRequest(
                installationId = "installation-1",
                deviceToken = "fcm:token",
                appVersion = "1.3 (7)",
                locale = "ca-ES",
                environment = "production",
                platform = "android",
                minimumInterest = NotificationInterestLevel.MEDIUM,
                groupSelection = NotificationGroupSelection(NotificationGroupSelection.Mode.CUSTOM, listOf("Minyons")),
            ),
        )
        service.unregister(installationId = "installation-1", environment = "production", platform = "android")

        val registration = server.takeRequest()
        val body = Json.parseToJsonElement(registration.body!!.utf8()).jsonObject
        assertEquals("PUT", registration.method)
        assertEquals("/service/v1/push-subscriptions/installation-1", registration.url.encodedPath)
        assertEquals("fcm:token", body.getValue("device_token").jsonPrimitive.content)
        assertEquals("1.3 (7)", body.getValue("app_version").jsonPrimitive.content)
        assertEquals("android", body.getValue("platform").jsonPrimitive.content)
        assertEquals("com.ahuguet.castellsenvena.internal", body.getValue("app_id").jsonPrimitive.content)
        assertEquals("medium", body.getValue("minimum_interest").jsonPrimitive.content)
        val selection = body.getValue("group_selection") as JsonObject
        assertEquals("custom", selection.getValue("mode").jsonPrimitive.content)
        assertEquals("minyons", selection.getValue("keys").jsonArray.single().jsonPrimitive.content)

        val removal = server.takeRequest()
        assertEquals("DELETE", removal.method)
        assertEquals("production", removal.url.queryParameter("environment"))
        assertEquals("android", removal.url.queryParameter("platform"))
        assertEquals("com.ahuguet.castellsenvena.internal", removal.url.queryParameter("app_id"))
    }

    private companion object {
        const val EMPTY_AGENDA =
            """{"items":[],"next_cursor":null,"official_url":"https://castellscat.cat/ca/agenda","from_cache":false,"source_status":"active"}"""
    }
}
