package com.ahuguet.castellsenvena.feature.calculator.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Forum
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ContentCard
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.core.domain.chat.ChatConversationSummary
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationAgeFormatter
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import java.time.Instant
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ConversationListScreen(
    model: ConversationListViewModel,
    actionScope: CoroutineScope,
    onOpen: (String) -> Unit,
    onCreate: () -> Unit,
) {
    val state by model.state.collectAsState()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()
    val snackbarHostState = remember { SnackbarHostState() }
    // The ages ("29 min") move on while the list is open.
    val now by produceState(Instant.now()) {
        while (true) {
            delay(60_000)
            value = Instant.now()
        }
    }
    var renameTargetId by rememberSaveable { mutableStateOf<String?>(null) }
    var renameText by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(model) { model.reload() }
    LaunchedEffect(state.errorMessage) {
        state.errorMessage?.let { snackbarHostState.showSnackbar(it) }
    }

    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            TopAppBar(
                title = { Text("Calculadora") },
                scrollBehavior = scrollBehavior,
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onCreate,
                icon = { Icon(Icons.Outlined.Edit, contentDescription = null) },
                text = { Text("Conversa nova") },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        if (state.conversations.isEmpty()) {
            ContentUnavailable(
                icon = Icons.Outlined.Forum,
                title = "Cap conversa",
                description = "Crea una conversa per comparar castells i actuacions.",
                modifier = Modifier.padding(padding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .padding(padding)
                    .fillMaxSize(),
                // Room for the button over the last row.
                contentPadding = PaddingValues(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 96.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(state.conversations, key = { conversation -> conversation.id }) { conversation ->
                    ConversationRow(
                        conversation = conversation,
                        now = now,
                        onClick = { onOpen(conversation.id) },
                        onRename = {
                            renameTargetId = conversation.id
                            renameText = conversation.title
                        },
                        onDelete = { actionScope.launch { model.delete(conversation.id) } },
                    )
                }
            }
        }
    }

    renameTargetId?.let { id ->
        RenameConversationDialog(
            title = renameText,
            onTitleChange = { renameText = it },
            onSave = {
                renameTargetId = null
                val title = renameText
                actionScope.launch { model.rename(id, title) }
            },
            onDismiss = { renameTargetId = null },
        )
    }
}

@Composable
private fun ConversationRow(
    conversation: ChatConversationSummary,
    now: Instant,
    onClick: () -> Unit,
    onRename: () -> Unit,
    onDelete: () -> Unit,
) {
    var showsMenu by remember { mutableStateOf(false) }
    ContentCard {
        ListItem(
            headlineContent = { Text(text = conversation.title, maxLines = 1, overflow = TextOverflow.Ellipsis) },
            modifier = Modifier
                .fillMaxWidth()
                .clickable(onClick = onClick)
                .semantics {
                    customActions = listOf(
                        CustomAccessibilityAction("Canvia el nom") { onRename(); true },
                        CustomAccessibilityAction("Elimina") { onDelete(); true },
                    )
                },
            supportingContent = { Text(ConversationAgeFormatter.format(conversation.updatedAt, now)) },
            trailingContent = {
                Box {
                    IconButton(onClick = { showsMenu = true }) {
                        Icon(Icons.Filled.MoreVert, contentDescription = "Opcions de la conversa")
                    }
                    DropdownMenu(expanded = showsMenu, onDismissRequest = { showsMenu = false }) {
                        DropdownMenuItem(
                            text = { Text("Canvia el nom") },
                            leadingIcon = { Icon(Icons.Outlined.Edit, contentDescription = null) },
                            onClick = {
                                showsMenu = false
                                onRename()
                            },
                        )
                        DropdownMenuItem(
                            text = { Text("Elimina") },
                            leadingIcon = { Icon(Icons.Outlined.Delete, contentDescription = null) },
                            colors = MenuDefaults.itemColors(
                                textColor = MaterialTheme.colorScheme.error,
                                leadingIconColor = MaterialTheme.colorScheme.error,
                            ),
                            onClick = {
                                showsMenu = false
                                onDelete()
                            },
                        )
                    }
                }
            },
            colors = ListItemDefaults.colors(containerColor = Color.Transparent),
        )
    }
}

@Composable
private fun RenameConversationDialog(
    title: String,
    onTitleChange: (String) -> Unit,
    onSave: () -> Unit,
    onDismiss: () -> Unit,
) {
    val focusRequester = remember { FocusRequester() }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Canvia el nom") },
        text = {
            OutlinedTextField(
                value = title,
                onValueChange = onTitleChange,
                label = { Text("Títol") },
                singleLine = true,
                modifier = Modifier.focusRequester(focusRequester),
            )
            LaunchedEffect(focusRequester) { focusRequester.requestFocus() }
        },
        confirmButton = { TextButton(onClick = onSave) { Text("Desa") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel·la") } },
    )
}
