@file:OptIn(ExperimentalCoroutinesApi::class)

package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.domain.chat.ChatConversation
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversationSummary
import com.ahuguet.castellsenvena.core.domain.chat.ChatMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.MessageDeliveryState
import java.io.IOException
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

class ChatViewModelTest {
    @Test
    fun sendingShowsTheUserMessageImmediatelyAndHidesSuggestions() = runTest {
        val repository = SuspendedChatRepository()
        val model = ChatViewModel(repository, conversationId = null)

        val sending = launch { model.send("  Què val el 5d9f?  ") }
        runCurrent()
        assertTrue(repository.didStartSending)

        val state = model.state.value
        assertTrue(state.isSending)
        assertFalse(state.showsPromptSuggestions)
        assertEquals(1, state.displayedMessages.size)
        assertEquals(ChatRole.USER, state.displayedMessages.single().role)
        assertEquals("Què val el 5d9f?", state.displayedMessages.single().content)
        assertEquals(MessageDeliveryState.SENDING, state.displayedMessages.single().deliveryState)
        assertFalse(model.canSend("Una altra pregunta"))

        repository.finishSending()
        sending.join()

        assertFalse(model.state.value.isSending)
        assertEquals(listOf(ChatRole.USER, ChatRole.ASSISTANT), model.state.value.displayedMessages.map { it.role })
        assertNull(model.state.value.pendingUserMessage)
    }

    @Test
    fun creatingAConversationNotifiesTheListBeforeTheResponseArrives() = runTest {
        val repository = SuspendedChatRepository()
        val created = mutableListOf<String>()
        val model = ChatViewModel(repository, conversationId = null, onConversationCreated = { created += it })

        val sending = launch { model.send("Què val el 5d9f?") }
        runCurrent()

        assertEquals(listOf(repository.conversationId), created)
        assertEquals(repository.conversationId, model.conversationId)
        repository.finishSending()
        sending.join()
    }

    @Test
    fun reopeningAConversationRefreshesUntilThePendingResponseArrives() = runTest {
        val repository = ReopenedChatRepository()
        val model = ChatViewModel(
            repository,
            conversationId = repository.conversationId,
            sleep = { repository.finishSending() },
        )

        model.loadFollowingPendingResponse()

        assertEquals(2, repository.loadCount)
        assertFalse(model.state.value.isSending)
        assertEquals(listOf(ChatRole.USER, ChatRole.ASSISTANT), model.state.value.displayedMessages.map { it.role })
        assertEquals("Resposta recuperada", model.state.value.displayedMessages.last().content)
    }

    @Test
    fun aFailedSendShowsTheErrorAndTheStoredMessage() = runTest {
        val repository = ReopenedChatRepository(failSending = true)
        val model = ChatViewModel(repository, conversationId = repository.conversationId)

        model.send("Què val el 5d9f?")

        assertEquals("S'ha produït un error inesperat.", model.state.value.errorMessage)
        assertFalse(model.state.value.isSending)
        assertNull(model.state.value.pendingUserMessage)
        assertTrue(model.canSend("Torna-ho a provar"))
    }

    @Test
    fun blankDraftsAreNotSent() = runTest {
        val repository = SuspendedChatRepository()
        val model = ChatViewModel(repository, conversationId = null)

        model.send("   ")

        assertFalse(repository.didStartSending)
        assertFalse(model.canSend(" "))
        assertTrue(model.state.value.showsPromptSuggestions)
        assertEquals("Conversa nova", model.state.value.title)
    }

    @Test
    fun messagesOverTheBackendLimitAreNeitherSentNorStored() = runTest {
        val repository = SuspendedChatRepository()
        val model = ChatViewModel(repository, conversationId = null)
        val longest = "a".repeat(ChatViewModel.MAX_MESSAGE_LENGTH)

        assertTrue(model.canSend(longest))
        assertFalse(model.canSend(longest + "a"))

        model.send(longest + "a")

        assertFalse(repository.didStartSending)
        assertTrue(model.state.value.displayedMessages.isEmpty())
        assertEquals("El missatge pot tenir fins a 2.000 caràcters.", model.state.value.errorMessage)
    }

    @Test
    fun conversationListReloadsAfterRenamingAndDeleting() = runTest {
        val repository = ReopenedChatRepository()
        val model = ConversationListViewModel(repository)

        model.reload()
        assertEquals(listOf("Què val el 5d9f?"), model.state.value.conversations.map { it.title })

        model.rename(repository.conversationId, "Concurs")
        assertEquals(listOf("Concurs"), model.state.value.conversations.map { it.title })

        model.delete(repository.conversationId)
        assertTrue(model.state.value.conversations.isEmpty())
    }

    private class SuspendedChatRepository : ChatRepository {
        val conversationId = "conversation-1"
        var didStartSending = false
        private val response = CompletableDeferred<ChatConversation>()
        private val now = Instant.parse("2026-07-21T10:00:00Z")

        override suspend fun listConversations(): List<ChatConversationSummary> = emptyList()
        override suspend fun createConversation(title: String): String = conversationId
        override suspend fun loadConversation(id: String) = ChatConversation(id, "Conversa nova", now, now, emptyList())
        override suspend fun renameConversation(id: String, title: String) = Unit
        override suspend fun deleteConversation(id: String) = Unit

        override suspend fun send(message: String, conversationId: String): ChatConversation {
            didStartSending = true
            return response.await()
        }

        override suspend fun retry(messageId: String, conversationId: String) = loadConversation(conversationId)

        fun finishSending() {
            response.complete(
                ChatConversation(
                    id = conversationId,
                    title = "Què val el 5d9f?",
                    createdAt = now,
                    updatedAt = now,
                    messages = listOf(
                        ChatMessage("user", ChatRole.USER, "Què val el 5d9f?", now, MessageDeliveryState.SENT),
                        ChatMessage("assistant", ChatRole.ASSISTANT, "Resposta", now, MessageDeliveryState.SENT),
                    ),
                ),
            )
        }
    }

    private class ReopenedChatRepository(private val failSending: Boolean = false) : ChatRepository {
        val conversationId = "conversation-1"
        var loadCount = 0
        private var responseIsReady = false
        private var title = "Què val el 5d9f?"
        private var deleted = false
        private val now = Instant.parse("2026-07-21T10:00:00Z")

        override suspend fun listConversations(): List<ChatConversationSummary> =
            if (deleted) emptyList() else listOf(ChatConversationSummary(conversationId, title, now, now))

        override suspend fun createConversation(title: String): String = conversationId

        override suspend fun loadConversation(id: String): ChatConversation {
            loadCount += 1
            val messages = buildList {
                add(
                    ChatMessage(
                        id = "user",
                        role = ChatRole.USER,
                        content = "Què val el 5d9f?",
                        createdAt = now,
                        deliveryState = when {
                            failSending -> MessageDeliveryState.FAILED
                            responseIsReady -> MessageDeliveryState.SENT
                            else -> MessageDeliveryState.SENDING
                        },
                    ),
                )
                if (responseIsReady) {
                    add(ChatMessage("assistant", ChatRole.ASSISTANT, "Resposta recuperada", now, MessageDeliveryState.SENT))
                }
            }
            return ChatConversation(id, title, now, now, messages)
        }

        override suspend fun renameConversation(id: String, title: String) {
            this.title = title
        }

        override suspend fun deleteConversation(id: String) {
            deleted = true
        }

        override suspend fun send(message: String, conversationId: String): ChatConversation {
            if (failSending) throw IOException("offline")
            finishSending()
            return loadConversation(conversationId)
        }

        override suspend fun retry(messageId: String, conversationId: String) = loadConversation(conversationId)

        fun finishSending() {
            responseIsReady = true
        }
    }
}
