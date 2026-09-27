package com.ahuguet.castellsenvena.core.network.dto

import com.ahuguet.castellsenvena.core.domain.chat.ChatPresentationResponse
import com.ahuguet.castellsenvena.core.domain.chat.ChatRequest
import com.ahuguet.castellsenvena.core.domain.chat.ChatResponse
import com.ahuguet.castellsenvena.core.domain.chat.PerformanceResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoreRankingRowResponse
import com.ahuguet.castellsenvena.core.domain.chat.ScoredCastellResponse
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal data class ChatRequestDto(
    @SerialName("conversation_id") val conversationId: String,
    @SerialName("installation_id") val installationId: String,
    val locale: String,
    val ruleset: String,
    val messages: List<ChatMessageDto>,
) {
    constructor(request: ChatRequest) : this(
        conversationId = request.conversationId,
        installationId = request.installationId,
        locale = request.locale,
        ruleset = request.ruleset,
        // A stored message over the limit must not make every later request fail.
        messages = request.messages
            .takeLast(ChatRequest.MAX_MESSAGES)
            .map { message ->
                ChatMessageDto(
                    role = message.role.wireValue,
                    content = message.content.take(ChatRequest.MAX_MESSAGE_LENGTH),
                )
            },
    )
}

@Serializable
internal data class ChatMessageDto(
    val role: String,
    val content: String,
)

@Serializable
internal data class ScoredCastellDto(
    val input: String,
    val canonical: String? = null,
    val outcome: String,
    val points: Int,
    val counted: Boolean,
    val reason: String? = null,
)

@Serializable
internal data class PerformanceDto(
    val label: String,
    val total: Int,
    val castells: List<ScoredCastellDto>,
)

@Serializable
internal data class ScoreRankingRowDto(
    val position: Int,
    val notation: String,
    @SerialName("loaded_points") val loadedPoints: Int,
    @SerialName("unloaded_points") val unloadedPoints: Int,
)

@Serializable
internal data class ChatPresentationDto(
    val type: String,
    val title: String,
    val outcome: String,
    @SerialName("focus_notation") val focusNotation: String? = null,
    val rows: List<ScoreRankingRowDto>,
)

@Serializable
internal data class ChatResponseDto(
    val reply: String,
    val intent: String,
    val performances: List<PerformanceDto>,
    @SerialName("winner_label") val winnerLabel: String? = null,
    val warnings: List<String> = emptyList(),
    @SerialName("ruleset_version") val rulesetVersion: String,
    @SerialName("needs_clarification") val needsClarification: Boolean,
    /** Absent in answers stored before structured presentations existed. */
    val presentation: ChatPresentationDto? = null,
) {
    fun toDomain() = ChatResponse(
        reply = reply,
        intent = intent,
        performances = performances.map { performance ->
            PerformanceResponse(
                label = performance.label,
                total = performance.total,
                castells = performance.castells.map { castell ->
                    ScoredCastellResponse(
                        input = castell.input,
                        canonical = castell.canonical,
                        outcome = castell.outcome,
                        points = castell.points,
                        counted = castell.counted,
                        reason = castell.reason,
                    )
                },
            )
        },
        winnerLabel = winnerLabel,
        warnings = warnings,
        rulesetVersion = rulesetVersion,
        needsClarification = needsClarification,
        presentation = presentation?.let { source ->
            ChatPresentationResponse(
                type = source.type,
                title = source.title,
                outcome = source.outcome,
                focusNotation = source.focusNotation,
                rows = source.rows.map { row ->
                    ScoreRankingRowResponse(
                        position = row.position,
                        notation = row.notation,
                        loadedPoints = row.loadedPoints,
                        unloadedPoints = row.unloadedPoints,
                    )
                },
            )
        },
    )

    companion object {
        fun from(response: ChatResponse) = ChatResponseDto(
            reply = response.reply,
            intent = response.intent,
            performances = response.performances.map { performance ->
                PerformanceDto(
                    label = performance.label,
                    total = performance.total,
                    castells = performance.castells.map { castell ->
                        ScoredCastellDto(
                            input = castell.input,
                            canonical = castell.canonical,
                            outcome = castell.outcome,
                            points = castell.points,
                            counted = castell.counted,
                            reason = castell.reason,
                        )
                    },
                )
            },
            winnerLabel = response.winnerLabel,
            warnings = response.warnings,
            rulesetVersion = response.rulesetVersion,
            needsClarification = response.needsClarification,
            presentation = response.presentation?.let { source ->
                ChatPresentationDto(
                    type = source.type,
                    title = source.title,
                    outcome = source.outcome,
                    focusNotation = source.focusNotation,
                    rows = source.rows.map { row ->
                        ScoreRankingRowDto(
                            position = row.position,
                            notation = row.notation,
                            loadedPoints = row.loadedPoints,
                            unloadedPoints = row.unloadedPoints,
                        )
                    },
                )
            },
        )
    }
}
