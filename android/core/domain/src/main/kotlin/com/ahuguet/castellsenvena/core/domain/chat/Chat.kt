package com.ahuguet.castellsenvena.core.domain.chat

import com.ahuguet.castellsenvena.core.common.UserFacingFailure
import java.time.Instant

enum class ChatRole(val wireValue: String) {
    USER("user"),
    ASSISTANT("assistant"),
    ;

    companion object {
        fun fromWireValue(value: String): ChatRole? = entries.firstOrNull { it.wireValue == value }
    }
}

enum class MessageDeliveryState(val storedValue: String) {
    SENDING("sending"),
    SENT("sent"),
    FAILED("failed"),
    ;

    companion object {
        fun fromStoredValue(value: String): MessageDeliveryState? =
            entries.firstOrNull { it.storedValue == value }
    }
}

data class ChatMessage(
    val id: String,
    val role: ChatRole,
    val content: String,
    val createdAt: Instant,
    val deliveryState: MessageDeliveryState,
    /** The structured answer behind an assistant message. */
    val calculation: ChatResponse? = null,
)

data class ChatConversationSummary(
    val id: String,
    val title: String,
    val createdAt: Instant,
    val updatedAt: Instant,
)

data class ChatConversation(
    val id: String,
    val title: String,
    val createdAt: Instant,
    val updatedAt: Instant,
    val messages: List<ChatMessage>,
)

data class ChatRequestMessage(
    val role: ChatRole,
    val content: String,
)

/** The backend only reads the latest [MAX_MESSAGES] messages of a conversation. */
data class ChatRequest(
    val conversationId: String,
    val installationId: String,
    val messages: List<ChatRequestMessage>,
    val locale: String = "ca-ES",
    val ruleset: String = "concurs-2026",
) {
    companion object {
        const val MAX_MESSAGES = 12
    }
}

data class ScoredCastellResponse(
    val input: String,
    val canonical: String?,
    val outcome: String,
    val points: Int,
    val counted: Boolean,
    val reason: String?,
)

data class PerformanceResponse(
    val label: String,
    val total: Int,
    val castells: List<ScoredCastellResponse>,
)

data class ScoreRankingRowResponse(
    val position: Int,
    val notation: String,
    val loadedPoints: Int,
    val unloadedPoints: Int,
)

data class ChatPresentationResponse(
    val type: String,
    val title: String,
    val outcome: String,
    val focusNotation: String?,
    val rows: List<ScoreRankingRowResponse>,
)

data class ChatResponse(
    val reply: String,
    val intent: String,
    val performances: List<PerformanceResponse>,
    val winnerLabel: String?,
    val warnings: List<String>,
    val rulesetVersion: String,
    val needsClarification: Boolean,
    val presentation: ChatPresentationResponse? = null,
)

/** Conversations are stored on the device only; the backend never persists them. */
interface ChatRepository {
    suspend fun listConversations(): List<ChatConversationSummary>
    suspend fun createConversation(title: String): String
    suspend fun loadConversation(id: String): ChatConversation
    suspend fun renameConversation(id: String, title: String)
    suspend fun deleteConversation(id: String)
    suspend fun send(message: String, conversationId: String): ChatConversation
    suspend fun retry(messageId: String, conversationId: String): ChatConversation
}

class ConversationNotFoundException : Exception("Conversation not found"), UserFacingFailure {
    override val userMessage: String = "No s'ha trobat la conversa."
}

class MessageNotFoundException : Exception("Message not found"), UserFacingFailure {
    override val userMessage: String = "No s'ha trobat el missatge."
}
