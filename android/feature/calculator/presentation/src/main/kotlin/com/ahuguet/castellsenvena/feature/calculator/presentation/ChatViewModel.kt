package com.ahuguet.castellsenvena.feature.calculator.presentation

import com.ahuguet.castellsenvena.core.common.userMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversation
import com.ahuguet.castellsenvena.core.domain.chat.ChatMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.MessageDeliveryState
import java.time.Clock
import java.util.UUID
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive

data class ChatState(
    val conversation: ChatConversation? = null,
    /** Shown at once, before the repository stores the message. */
    val pendingUserMessage: ChatMessage? = null,
    val isSending: Boolean = false,
    val errorMessage: String? = null,
) {
    val displayedMessages: List<ChatMessage>
        get() = conversation?.messages.orEmpty() + listOfNotNull(pendingUserMessage)

    val showsPromptSuggestions: Boolean get() = displayedMessages.isEmpty() && !isSending

    val title: String get() = conversation?.title ?: NEW_CONVERSATION_TITLE

    companion object {
        const val NEW_CONVERSATION_TITLE = "Conversa nova"
    }
}

/** One calculator conversation. A new conversation is created with its first message. */
class ChatViewModel(
    private val repository: ChatRepository,
    conversationId: String?,
    private val onConversationCreated: (String) -> Unit = {},
    private val sleep: suspend (Duration) -> Unit = { delay(it) },
    private val clock: Clock = Clock.systemUTC(),
    private val newId: () -> String = { UUID.randomUUID().toString() },
) {
    var conversationId: String? = conversationId
        private set

    private val mutableState = MutableStateFlow(ChatState())
    val state: StateFlow<ChatState> = mutableState.asStateFlow()

    fun canSend(text: String): Boolean = text.isNotBlank() && !mutableState.value.isSending

    suspend fun load() {
        val id = conversationId ?: return
        try {
            val conversation = repository.loadConversation(id)
            mutableState.update {
                it.copy(
                    conversation = conversation,
                    isSending = conversation.messages.any { message ->
                        message.role == ChatRole.USER && message.deliveryState == MessageDeliveryState.SENDING
                    },
                    errorMessage = null,
                )
            }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            mutableState.update { it.copy(errorMessage = failure.userMessage()) }
        }
    }

    /** A conversation reopened while its answer is on the way polls until it arrives. */
    suspend fun loadFollowingPendingResponse() {
        load()
        while (mutableState.value.isSending && currentCoroutineContext().isActive) {
            try {
                sleep(PENDING_RESPONSE_POLL_INTERVAL)
            } catch (_: Exception) {
                return
            }
            if (!currentCoroutineContext().isActive) return
            load()
        }
    }

    suspend fun send(text: String) {
        val message = text.trim()
        if (message.isEmpty() || mutableState.value.isSending) return
        mutableState.update {
            it.copy(
                pendingUserMessage = ChatMessage(
                    id = newId(),
                    role = ChatRole.USER,
                    content = message,
                    createdAt = clock.instant(),
                    deliveryState = MessageDeliveryState.SENDING,
                ),
                isSending = true,
                errorMessage = null,
            )
        }
        try {
            val id = conversationId ?: repository.createConversation(message).also { created ->
                conversationId = created
                onConversationCreated(created)
            }
            val conversation = repository.send(message, id)
            mutableState.update { it.copy(pendingUserMessage = null, conversation = conversation) }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            // Reload first: the stored message now offers a retry, and the error stays visible.
            mutableState.update { it.copy(pendingUserMessage = null) }
            load()
            mutableState.update { it.copy(errorMessage = failure.userMessage()) }
        } finally {
            mutableState.update { it.copy(isSending = false) }
        }
    }

    suspend fun retry(messageId: String) {
        val id = conversationId ?: return
        if (mutableState.value.isSending) return
        mutableState.update { it.copy(isSending = true, errorMessage = null) }
        try {
            val conversation = repository.retry(messageId, id)
            mutableState.update { it.copy(conversation = conversation) }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            load()
            mutableState.update { it.copy(errorMessage = failure.userMessage()) }
        } finally {
            mutableState.update { it.copy(isSending = false) }
        }
    }

    private companion object {
        val PENDING_RESPONSE_POLL_INTERVAL = 250.milliseconds
    }
}
