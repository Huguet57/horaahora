package com.ahuguet.castellsenvena.feature.calculator.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.feature.calculator.presentation.ChatViewModel
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import java.util.UUID
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/**
 * An open chat. The session key identifies the chat on screen, so a new
 * conversation keeps its model when its first message creates it.
 */
@Immutable
private data class ChatDestination(val sessionKey: String, val conversationId: String?) {
    companion object {
        fun conversation(id: String) = ChatDestination(UUID.randomUUID().toString(), id)

        fun newConversation() = ChatDestination(UUID.randomUUID().toString(), null)

        val Saver = Saver<ChatDestination?, String>(
            save = { destination -> destination?.let { "${it.sessionKey}|${it.conversationId.orEmpty()}" } },
            restore = { saved ->
                val parts = saved.split('|', limit = 2)
                ChatDestination(sessionKey = parts[0], conversationId = parts.getOrNull(1)?.ifEmpty { null })
            },
        )
    }
}

/**
 * The calculator: the stored conversations and, above them, one open chat.
 * Messages are sent in [actionScope] so an answer on the way is kept even if
 * the chat is closed; reopening it follows the pending answer.
 */
@Composable
fun CalculatorScreen(
    repository: ChatRepository,
    listModel: ConversationListViewModel,
    actionScope: CoroutineScope,
    onChatVisibilityChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    var destination by rememberSaveable(stateSaver = ChatDestination.Saver) { mutableStateOf<ChatDestination?>(null) }
    val reduceMotion = LocalReduceMotion.current
    val isChatVisible = destination != null

    DisposableEffect(isChatVisible) {
        onChatVisibilityChange(isChatVisible)
        onDispose { onChatVisibilityChange(false) }
    }
    BackHandler(enabled = isChatVisible) { destination = null }

    AnimatedContent(
        targetState = destination,
        modifier = modifier,
        contentKey = { it?.sessionKey },
        transitionSpec = {
            when {
                reduceMotion -> EnterTransition.None togetherWith ExitTransition.None
                targetState != null -> (slideInHorizontally { it } togetherWith slideOutHorizontally { -it / 4 } + fadeOut())
                    .apply { targetContentZIndex = 1f }
                else -> (slideInHorizontally { -it / 4 } togetherWith slideOutHorizontally { it })
                    .apply { targetContentZIndex = -1f }
            }
        },
        label = "calculator",
    ) { target ->
        if (target == null) {
            ConversationListScreen(
                model = listModel,
                actionScope = actionScope,
                onOpen = { id -> destination = ChatDestination.conversation(id) },
                onCreate = { destination = ChatDestination.newConversation() },
            )
        } else {
            val chatModel = remember(target.sessionKey) {
                ChatViewModel(
                    repository = repository,
                    conversationId = target.conversationId,
                    onConversationCreated = { id ->
                        // Only while this chat is still the one on screen.
                        destination = destination
                            ?.takeIf { it.sessionKey == target.sessionKey }
                            ?.copy(conversationId = id)
                            ?: destination
                        actionScope.launch { listModel.reload() }
                    },
                )
            }
            ChatRoute(
                model = chatModel,
                sessionKey = target.sessionKey,
                actionScope = actionScope,
                onBack = { destination = null },
            )
        }
    }
}
