package com.ahuguet.castellsenvena.feature.calculator.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.core.designsystem.component.SkeletonBlock
import com.ahuguet.castellsenvena.core.designsystem.component.rememberPulseAlpha
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.calculator.presentation.CalculatorPrompts
import com.ahuguet.castellsenvena.feature.calculator.presentation.ChatState
import com.ahuguet.castellsenvena.feature.calculator.presentation.ChatViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

private const val SkeletonKey = "assistant-response-skeleton"
private const val SuggestionsKey = "prompt-suggestions"

/** Connects a chat model to its screen; messages go out in [actionScope]. */
@Composable
internal fun ChatRoute(model: ChatViewModel, sessionKey: String, actionScope: CoroutineScope, onBack: () -> Unit) {
    val state by model.state.collectAsState()
    var draft by rememberSaveable(sessionKey) { mutableStateOf("") }

    LaunchedEffect(model) { model.loadFollowingPendingResponse() }

    ChatScreen(
        state = state,
        draft = draft,
        onDraftChange = { draft = it },
        canSend = model.canSend(draft),
        onSend = {
            val text = draft
            if (model.canSend(text)) {
                draft = ""
                actionScope.launch { model.send(text) }
            }
        },
        onSuggestion = { prompt ->
            draft = ""
            actionScope.launch { model.send(prompt) }
        },
        onRetry = { messageId -> actionScope.launch { model.retry(messageId) } },
        onBack = onBack,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChatScreen(
    state: ChatState,
    draft: String,
    onDraftChange: (String) -> Unit,
    canSend: Boolean,
    onSend: () -> Unit,
    onSuggestion: (String) -> Unit,
    onRetry: (String) -> Unit,
    onBack: () -> Unit,
) {
    val listState = rememberLazyListState()
    val focusManager = LocalFocusManager.current
    val reduceMotion = LocalReduceMotion.current
    // Dragging the conversation puts the keyboard away.
    val dismissKeyboardOnDrag = remember(focusManager) {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                if (source == NestedScrollSource.UserInput) focusManager.clearFocus()
                return Offset.Zero
            }
        }
    }

    // The list is reversed: item 0 is the newest message, at the bottom.
    val newestKey = if (state.isSending) SkeletonKey else state.displayedMessages.lastOrNull()?.id
    LaunchedEffect(newestKey) {
        if (newestKey == null) return@LaunchedEffect
        if (reduceMotion) listState.scrollToItem(0) else listState.animateScrollToItem(0)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(state.title, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Enrere")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .consumeWindowInsets(padding)
                .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Horizontal)),
        ) {
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .nestedScroll(dismissKeyboardOnDrag)
                    .pointerInput(focusManager) { detectTapGestures { focusManager.clearFocus() } },
                reverseLayout = true,
                verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.Top),
                contentPadding = PaddingValues(16.dp),
            ) {
                if (state.isSending) {
                    item(key = SkeletonKey) { AssistantResponseSkeleton() }
                }
                items(state.displayedMessages.asReversed(), key = { it.id }, contentType = { "message" }) { message ->
                    MessageBubble(
                        message = message,
                        onRetry = { onRetry(message.id) },
                        modifier = if (reduceMotion) Modifier else Modifier.animateItem(),
                    )
                }
                if (state.showsPromptSuggestions) {
                    item(key = SuggestionsKey) { PromptSuggestions(onSelect = onSuggestion) }
                }
            }

            state.errorMessage?.let { message ->
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 4.dp),
                )
            }

            Composer(draft = draft, onDraftChange = onDraftChange, canSend = canSend, onSend = onSend)
        }
    }
}

@Composable
private fun Composer(draft: String, onDraftChange: (String) -> Unit, canSend: Boolean, onSend: () -> Unit) {
    Surface(color = MaterialTheme.colorScheme.surfaceContainer) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                // Above the navigation bar, or above the keyboard while it is open.
                .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom))
                .padding(horizontal = 16.dp, vertical = 10.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            val length = draft.trim().length
            val limit = ChatViewModel.MAX_MESSAGE_LENGTH
            OutlinedTextField(
                value = draft,
                onValueChange = onDraftChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Pregunta o escriu dues actuacions…") },
                // The count appears near the limit the backend accepts.
                isError = length > limit,
                supportingText = if (length > limit - 200) {
                    { Text("${CatalanNumbers.grouped(length)}/${CatalanNumbers.grouped(limit)}") }
                } else {
                    null
                },
                maxLines = 5,
                shape = RoundedCornerShape(22.dp),
                keyboardOptions = KeyboardOptions(
                    capitalization = KeyboardCapitalization.Sentences,
                    autoCorrectEnabled = false,
                    imeAction = ImeAction.Send,
                ),
                keyboardActions = KeyboardActions(onSend = { onSend() }),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                ),
            )
            FilledIconButton(onClick = onSend, enabled = canSend, modifier = Modifier.padding(bottom = 4.dp)) {
                Icon(Icons.Filled.ArrowUpward, contentDescription = "Envia")
            }
        }
    }
}

@Composable
private fun PromptSuggestions(onSelect: (String) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Prova una comparació", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        for (prompt in CalculatorPrompts.suggestions) {
            FilledTonalButton(
                onClick = { onSelect(prompt) },
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.filledTonalButtonColors(
                    containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                    contentColor = MaterialTheme.colorScheme.primary,
                ),
                contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
            ) {
                Text(prompt, textAlign = TextAlign.Start)
            }
        }
    }
}

/** Stands for the answer while it is on the way. */
@Composable
private fun AssistantResponseSkeleton() {
    val alpha = rememberPulseAlpha()
    val divider = MaterialTheme.colorScheme.outlineVariant
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clearAndSetSemantics { contentDescription = "Preparant la resposta" },
    ) {
        Surface(
            modifier = Modifier
                .weight(1f, fill = false)
                .widthIn(max = 360.dp)
                .alpha(alpha),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surfaceContainerHigh,
        ) {
            Column(modifier = Modifier.padding(11.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                SkeletonBlock(width = 205.dp, height = 17.dp)
                HorizontalDivider(color = divider)
                Row(horizontalArrangement = Arrangement.spacedBy(7.dp), verticalAlignment = Alignment.CenterVertically) {
                    SkeletonBlock(width = 18.dp, height = 18.dp)
                    SkeletonBlock(width = 88.dp, height = 13.dp)
                }
                Column(
                    modifier = Modifier
                        .clip(RoundedCornerShape(11.dp))
                        .background(MaterialTheme.colorScheme.onSurface.copy(alpha = 0.04f))
                        .padding(10.dp),
                    verticalArrangement = Arrangement.spacedBy(9.dp),
                ) {
                    SkeletonTableRow(first = 56.dp to 12.dp, cell = 82.dp to 12.dp)
                    HorizontalDivider(color = divider)
                    SkeletonTableRow(first = 14.dp to 12.dp, cell = 76.dp to 30.dp)
                    HorizontalDivider(color = divider)
                    SkeletonTableRow(first = 42.dp to 13.dp, cell = 64.dp to 13.dp)
                }
                SkeletonBlock(width = 150.dp, height = 13.dp)
            }
        }
        Spacer(Modifier.width(44.dp))
    }
}

@Composable
private fun SkeletonTableRow(
    first: Pair<Dp, Dp>,
    cell: Pair<Dp, Dp>,
) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        SkeletonBlock(width = first.first, height = first.second)
        Spacer(Modifier.weight(1f))
        SkeletonBlock(width = cell.first, height = cell.second)
        SkeletonBlock(width = cell.first, height = cell.second)
    }
}
