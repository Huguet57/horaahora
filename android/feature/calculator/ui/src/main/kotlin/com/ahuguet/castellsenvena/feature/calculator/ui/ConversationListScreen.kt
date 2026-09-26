package com.ahuguet.castellsenvena.feature.calculator.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
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
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedDivider
import com.ahuguet.castellsenvena.core.designsystem.component.groupedItemShape
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
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
    val scrollBehavior = TopAppBarDefaults.exitUntilCollapsedScrollBehavior()
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
            LargeTopAppBar(
                title = { Text("Calculadora") },
                scrollBehavior = scrollBehavior,
                colors = TopAppBarDefaults.largeTopAppBarColors(
                    containerColor = CastellsTheme.colors.groupedBackground,
                    scrolledContainerColor = CastellsTheme.colors.groupedBackground,
                ),
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
        containerColor = CastellsTheme.colors.groupedBackground,
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
                contentPadding = PaddingValues(top = 8.dp, bottom = 96.dp),
            ) {
                itemsIndexed(state.conversations, key = { _, conversation -> conversation.id }) { index, conversation ->
                    ConversationRow(
                        conversation = conversation,
                        now = now,
                        shape = groupedItemShape(index, state.conversations.size),
                        showsDivider = index < state.conversations.lastIndex,
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
    shape: Shape,
    showsDivider: Boolean,
    onClick: () -> Unit,
    onRename: () -> Unit,
    onDelete: () -> Unit,
) {
    var showsMenu by remember { mutableStateOf(false) }
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = shape,
        color = CastellsTheme.colors.groupedCard,
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(onClick = onClick)
                    .semantics {
                        customActions = listOf(
                            CustomAccessibilityAction("Canvia el nom") { onRename(); true },
                            CustomAccessibilityAction("Elimina") { onDelete(); true },
                        )
                    }
                    .padding(start = 16.dp, top = 10.dp, bottom = 10.dp, end = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text(
                        text = conversation.title,
                        style = MaterialTheme.typography.bodyLarge,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = ConversationAgeFormatter.format(conversation.updatedAt, now),
                        style = MaterialTheme.typography.bodySmall,
                        color = CastellsTheme.colors.secondaryText,
                    )
                }
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
            }
            if (showsDivider) GroupedDivider()
        }
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
