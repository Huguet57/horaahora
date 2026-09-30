package com.ahuguet.castellsenvena.core.data

import com.ahuguet.castellsenvena.core.data.chat.DatabaseChatRepository
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.ConversationNotFoundException
import com.ahuguet.castellsenvena.core.domain.chat.MessageDeliveryState
import com.ahuguet.castellsenvena.core.domain.chat.PerformanceResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoredCastellResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScenarioPerformance
import com.ahuguet.castellsenvena.core.network.service.ChatRemoteService
import java.io.IOException
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest

class ChatPersistenceTest {
    @Test
    fun conversationPersistsCanBeRenamedAndDeleted() = runTest {
        val database = inMemoryDatabase()
        val remote = StubChatRemoteService()
        val repository = repository(database, remote)

        val id = repository.createConversation("Primera conversa")
        repository.send("5d9f o 4d9fa?", id)
        assertEquals("test-installation", remote.requests.single().installationId)

        val reopened = repository(database, remote)
        val conversation = reopened.loadConversation(id)
        assertEquals(listOf(ChatRole.USER, ChatRole.ASSISTANT), conversation.messages.map { it.role })
        assertEquals("Guanya 4de9fa.", conversation.messages.last().content)
        assertEquals(4105, conversation.messages.last().calculation?.performances?.single()?.total)

        reopened.renameConversation(id, "Concurs")
        assertEquals("Concurs", reopened.listConversations().first().title)

        reopened.deleteConversation(id)
        assertTrue(reopened.listConversations().isEmpty())
        assertFailsWith<ConversationNotFoundException> { reopened.loadConversation(id) }
    }

    @Test
    fun titlesAreTrimmedShortenedAndNeverEmpty() = runTest {
        val repository = repository(inMemoryDatabase(), StubChatRemoteService())

        val untitled = repository.createConversation("   ")
        val long = repository.createConversation("  " + "a".repeat(60))

        assertEquals("Conversa nova", repository.loadConversation(untitled).title)
        assertEquals("a".repeat(48), repository.loadConversation(long).title)
    }

    @Test
    fun failedDeliveriesAreMarkedAndCanBeRetried() = runTest {
        val remote = StubChatRemoteService(failures = 1)
        val repository = repository(inMemoryDatabase(), remote)
        val id = repository.createConversation("Pregunta")

        assertFailsWith<IOException> { repository.send("  Què val el 5d9f?  ", id) }
        val failed = repository.loadConversation(id).messages.single()
        assertEquals(MessageDeliveryState.FAILED, failed.deliveryState)
        assertEquals("Què val el 5d9f?", failed.content)

        val answered = repository.retry(failed.id, id)

        assertEquals(listOf(MessageDeliveryState.SENT, MessageDeliveryState.SENT), answered.messages.map { it.deliveryState })
        assertEquals(listOf(ChatRole.USER, ChatRole.ASSISTANT), answered.messages.map { it.role })
    }

    @Test
    fun onlyTheLatestTwelveMessagesAreSent() = runTest {
        val remote = StubChatRemoteService()
        val repository = repository(inMemoryDatabase(), remote)
        val id = repository.createConversation("Llarga")

        repeat(7) { repository.send("Pregunta $it", id) }

        val lastRequest = remote.requests.last()
        assertEquals(ChatRequest.MAX_MESSAGES, lastRequest.messages.size)
        assertEquals("Pregunta 6", lastRequest.messages.last().content)
        assertEquals(ChatRole.USER, lastRequest.messages.last().role)
    }

    @Test
    fun completeScenarioSurvivesHistoryWindowAndReopening() = runTest {
        val database = inMemoryDatabase()
        val remote = StubChatRemoteService()
        val repository = repository(database, remote)
        val castells = listOf(
            ScoredCastellResponse("3d10fm", "3de10fm", "loaded", 100, true, null),
            ScoredCastellResponse("4d9fa", "4de9fa", "loaded", 90, true, null),
            ScoredCastellResponse("5d9f", "5de9f", "loaded", 80, false, "loaded_limit"),
            ScoredCastellResponse("4d8", "4de8", "unloaded", 70, true, null),
            ScoredCastellResponse("3d8", "3de8", "unloaded", 60, false, "outside_top_three"),
            ScoredCastellResponse("9d9f", "9de9f", "attempt", 0, false, "attempt"),
        )
        val original = listOf(PerformanceResponse("Vella", 260, castells))
        remote.performances = original
        val id = repository.createConversation("Llarga")
        repository.send("Escenari original", id)
        remote.performances = emptyList()
        repeat(6) { repository.send("Hola", id) }
        val reopened = repository(database, remote)
        reopened.send("I si descarreguen el 5d9f?", id)
        val request = remote.requests.last()
        assertEquals(12, request.messages.size)
        assertTrue(request.messages.none { it.content == "Escenari original" })
        assertEquals(original.map(::ScenarioPerformance), request.scenario)

        val replacement = listOf(PerformanceResponse("Nou", 100, castells.take(1)))
        remote.performances = replacement
        reopened.send("Comencem de nou: 3d10fm carregat", id)
        reopened.send("I descarregat?", id)
        assertEquals(replacement.map(::ScenarioPerformance), remote.requests.last().scenario)
        val other = reopened.createConversation("Una altra")
        reopened.send("Hola", other)
        assertTrue(remote.requests.last().scenario.isEmpty())
    }

    private fun TestScope.repository(database: CastellsDatabase, remote: ChatRemoteService) =
        DatabaseChatRepository(
            database = database,
            remoteService = remote,
            installationId = "test-installation",
            clock = Clock.fixed(Instant.parse("2026-07-21T10:00:00Z"), ZoneOffset.UTC),
            // Like the app: a failed delivery must not cancel the scope.
            deliveryScope = CoroutineScope(SupervisorJob()),
            ioDispatcher = StandardTestDispatcher(testScheduler),
        )

    private class StubChatRemoteService(private var failures: Int = 0) : ChatRemoteService {
        val requests = mutableListOf<ChatRequest>()
        var performances: List<PerformanceResponse>? = null

        override suspend fun send(request: ChatRequest): ChatResponse {
            requests += request
            if (failures > 0) {
                failures -= 1
                throw offline()
            }
            return ChatResponse(
                reply = "Guanya 4de9fa.",
                intent = "comparison",
                performances = performances ?: listOf(
                    PerformanceResponse(
                        label = "4de9fa",
                        total = 4105,
                        castells = listOf(ScoredCastellResponse("4d9fa", "4de9fa", "unloaded", 4105, true, null)),
                    ),
                ),
                winnerLabel = "4de9fa",
                warnings = emptyList(),
                rulesetVersion = "concurs-2026",
                needsClarification = false,
            )
        }
    }
}
