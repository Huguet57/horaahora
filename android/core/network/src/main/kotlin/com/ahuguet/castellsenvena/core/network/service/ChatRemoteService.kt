package com.ahuguet.castellsenvena.core.network.service

import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.network.ApiClient
import com.ahuguet.castellsenvena.core.network.CastellsJson
import com.ahuguet.castellsenvena.core.network.dto.ChatRequestDto
import com.ahuguet.castellsenvena.core.network.dto.ChatResponseDto
import kotlinx.serialization.SerializationException

interface ChatRemoteService {
    suspend fun send(request: ChatRequest): ChatResponse
}

class HttpChatRemoteService(private val client: ApiClient) : ChatRemoteService {
    override suspend fun send(request: ChatRequest): ChatResponse =
        client.post(
            path = "/v1/chat",
            body = ChatRequestDto(request),
            serializer = ChatRequestDto.serializer(),
            deserializer = ChatResponseDto.serializer(),
        ).toDomain()
}

/**
 * Stores assistant answers in the same JSON the backend returns, so saved
 * conversations keep working when the app learns new presentations.
 */
object ChatResponseCodec {
    fun encode(response: ChatResponse): String =
        CastellsJson.encodeToString(ChatResponseDto.serializer(), ChatResponseDto.from(response))

    /** Null when the stored JSON is no longer readable. */
    fun decodeOrNull(json: String): ChatResponse? =
        try {
            CastellsJson.decodeFromString(ChatResponseDto.serializer(), json).toDomain()
        } catch (_: SerializationException) {
            null
        } catch (_: IllegalArgumentException) {
            null
        }
}
