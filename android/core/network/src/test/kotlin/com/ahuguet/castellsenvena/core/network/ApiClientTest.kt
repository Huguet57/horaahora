package com.ahuguet.castellsenvena.core.network

import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequestMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.ScenarioCastell
import com.ahuguet.castellsenvena.core.domain.chat.ScenarioPerformance
import com.ahuguet.castellsenvena.core.network.service.HttpChatRemoteService
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
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
    fun httpErrorsExposeTheServerDetail() = runTest {
        server.enqueue(MockResponse(code = 429, body = """{"detail":"Massa consultes. Torna-ho a provar."}"""))

        val failure = assertFailsWith<ApiException.Http> {
            client.probe()
        }

        assertEquals(429, failure.statusCode)
        assertEquals("Massa consultes. Torna-ho a provar.", failure.userMessage)
    }

    @Test
    fun validationErrorsWithoutATextDetailUseTheStatusMessage() = runTest {
        server.enqueue(MockResponse(code = 422, body = """{"detail":[{"msg":"invalid"}]}"""))

        val failure = assertFailsWith<ApiException.Http> {
            client.probe()
        }

        assertEquals("El servidor ha retornat l'error 422.", failure.userMessage)
    }

    @Test
    fun malformedResponsesAreReportedAsInvalid() = runTest {
        server.enqueue(MockResponse(body = """{"items": "not a list"}"""))

        val failure = assertFailsWith<ApiException.InvalidResponse> {
            client.probe()
        }

        assertEquals("La resposta del servidor no és vàlida.", failure.userMessage)
    }

    @Test
    fun unreachableServersAreReportedAsNetworkFailures() = runTest {
        val url = server.url("/").toString()
        server.close()

        val failure = assertFailsWith<ApiException.Network> {
            ApiClient(url).probe()
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
            ChatRequest(
                conversationId = "conversation", installationId = "installation", messages = messages,
                scenario = listOf(ScenarioPerformance("Vella", listOf(ScenarioCastell("5de9f", "attempt")))),
            ),
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
        val scenario = body.getValue("scenario").jsonArray.single().jsonObject
        assertEquals("Vella", scenario.getValue("label").jsonPrimitive.content)
        val castell = scenario.getValue("castells").jsonArray.single().jsonObject
        assertEquals("5de9f", castell.getValue("notation").jsonPrimitive.content)
        assertEquals("attempt", castell.getValue("outcome").jsonPrimitive.content)
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

    /** A body the client can decode, to exercise its error handling. */
    @Serializable
    private data class Probe(val items: List<String>)

    private suspend fun ApiClient.probe(): Probe =
        post(path = "/v1/probe", body = Probe(emptyList()), serializer = Probe.serializer(), deserializer = Probe.serializer())
}
