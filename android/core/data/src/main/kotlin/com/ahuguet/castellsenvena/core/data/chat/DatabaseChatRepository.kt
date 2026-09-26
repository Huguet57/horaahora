package com.ahuguet.castellsenvena.core.data.chat

import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.database.ConversationRecord
import com.ahuguet.castellsenvena.core.database.MessageRecord
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversation
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversationSummary
import com.ahuguet.castellsenvena.core.domain.chat.ChatMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequestMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.ConversationNotFoundException
import com.ahuguet.castellsenvena.core.domain.chat.MessageDeliveryState
import com.ahuguet.castellsenvena.core.domain.chat.MessageNotFoundException
import com.ahuguet.castellsenvena.core.network.service.ChatRemoteService
import com.ahuguet.castellsenvena.core.network.service.ChatResponseCodec
import java.time.Clock
import java.time.Instant
import java.util.UUID
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.withContext

/**
 * Keeps calculator conversations on the device. The backend only receives the
 * latest messages of the conversation being answered.
 */
class DatabaseChatRepository(
    private val database: CastellsDatabase,
    private val remoteService: ChatRemoteService,
    private val installationId: String,
    private val clock: Clock = Clock.systemUTC(),
    private val newId: () -> String = { UUID.randomUUID().toString() },
    /**
     * Deliveries run here so an answer is stored even when the screen that
     * asked for it is closed; reopening the conversation shows it.
     */
    private val deliveryScope: CoroutineScope = CoroutineScope(SupervisorJob()),
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ChatRepository {
    private val conversations get() = database.conversationRecordQueries
    private val messages get() = database.messageRecordQueries

    override suspend fun listConversations(): List<ChatConversationSummary> = withContext(ioDispatcher) {
        conversations.all().executeAsList().map { it.toSummary() }
    }

    override suspend fun createConversation(title: String): String = withContext(ioDispatcher) {
        val now = clock.millis()
        val id = newId()
        conversations.insert(ConversationRecord(id = id, title = cleanTitle(title), createdAt = now, updatedAt = now))
        id
    }

    override suspend fun loadConversation(id: String): ChatConversation = withContext(ioDispatcher) {
        thread(record(id))
    }

    override suspend fun renameConversation(id: String, title: String) = withContext(ioDispatcher) {
        record(id)
        conversations.rename(title = cleanTitle(title), updatedAt = clock.millis(), id = id)
        Unit
    }

    override suspend fun deleteConversation(id: String) = withContext(ioDispatcher) {
        record(id)
        database.transaction {
            messages.deleteForConversation(id)
            conversations.delete(id)
        }
    }

    override suspend fun send(message: String, conversationId: String): ChatConversation {
        val userMessageId = withContext(ioDispatcher) {
            record(conversationId)
            val now = clock.millis()
            val userMessage = MessageRecord(
                id = newId(),
                conversationId = conversationId,
                role = ChatRole.USER.wireValue,
                content = message.trim(),
                createdAt = now,
                deliveryState = MessageDeliveryState.SENDING.storedValue,
                calculationJson = null,
            )
            database.transaction {
                messages.insert(userMessage)
                conversations.touch(updatedAt = now, id = conversationId)
            }
            userMessage.id
        }
        return deliver(userMessageId, conversationId)
    }

    override suspend fun retry(messageId: String, conversationId: String): ChatConversation {
        withContext(ioDispatcher) {
            record(conversationId)
            val message = messages.byId(messageId, conversationId).executeAsOneOrNull()
            if (message == null || message.role != ChatRole.USER.wireValue) throw MessageNotFoundException()
            messages.updateDeliveryState(MessageDeliveryState.SENDING.storedValue, messageId)
        }
        return deliver(messageId, conversationId)
    }

    private suspend fun deliver(userMessageId: String, conversationId: String): ChatConversation =
        deliveryScope.async(ioDispatcher) {
            val history = messages.forConversation(conversationId).executeAsList()
            val request = ChatRequest(
                conversationId = conversationId,
                installationId = installationId,
                messages = history.takeLast(ChatRequest.MAX_MESSAGES).mapNotNull { message ->
                    ChatRole.fromWireValue(message.role)?.let { ChatRequestMessage(it, message.content) }
                },
            )
            try {
                val response = remoteService.send(request)
                val now = clock.millis()
                database.transaction {
                    messages.updateDeliveryState(MessageDeliveryState.SENT.storedValue, userMessageId)
                    messages.insert(
                        MessageRecord(
                            id = newId(),
                            conversationId = conversationId,
                            role = ChatRole.ASSISTANT.wireValue,
                            content = response.reply,
                            createdAt = now,
                            deliveryState = MessageDeliveryState.SENT.storedValue,
                            calculationJson = ChatResponseCodec.encode(response),
                        ),
                    )
                    conversations.touch(updatedAt = now, id = conversationId)
                }
                thread(record(conversationId))
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (failure: Exception) {
                runCatching {
                    database.transaction {
                        messages.updateDeliveryState(MessageDeliveryState.FAILED.storedValue, userMessageId)
                        conversations.touch(updatedAt = clock.millis(), id = conversationId)
                    }
                }
                throw failure
            }
        }.await()

    private fun record(id: String): ConversationRecord =
        conversations.byId(id).executeAsOneOrNull() ?: throw ConversationNotFoundException()

    private fun thread(record: ConversationRecord): ChatConversation = ChatConversation(
        id = record.id,
        title = record.title,
        createdAt = Instant.ofEpochMilli(record.createdAt),
        updatedAt = Instant.ofEpochMilli(record.updatedAt),
        messages = messages.forConversation(record.id).executeAsList().mapNotNull { it.toDomain() },
    )

    private companion object {
        const val MAX_TITLE_LENGTH = 48

        fun cleanTitle(title: String): String {
            val clean = title.trim()
            return if (clean.isEmpty()) "Conversa nova" else clean.take(MAX_TITLE_LENGTH)
        }

        fun ConversationRecord.toSummary() = ChatConversationSummary(
            id = id,
            title = title,
            createdAt = Instant.ofEpochMilli(createdAt),
            updatedAt = Instant.ofEpochMilli(updatedAt),
        )

        fun MessageRecord.toDomain(): ChatMessage? {
            val role = ChatRole.fromWireValue(role) ?: return null
            val state = MessageDeliveryState.fromStoredValue(deliveryState) ?: return null
            return ChatMessage(
                id = id,
                role = role,
                content = content,
                createdAt = Instant.ofEpochMilli(createdAt),
                deliveryState = state,
                calculation = calculationJson?.let(ChatResponseCodec::decodeOrNull),
            )
        }
    }
}
