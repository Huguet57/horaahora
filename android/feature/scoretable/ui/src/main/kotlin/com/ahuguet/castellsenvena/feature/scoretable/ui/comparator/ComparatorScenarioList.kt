package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.ContentCopy
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.StarBorder
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.input.pointer.PointerInputScope
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellNotation
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorScenario
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import kotlinx.coroutines.launch

private const val FAVORITES_HEADER = "header:favorits"
private const val OTHERS_HEADER = "header:escenaris"

/**
 * The comparator's main page: every scenario as who wins and each colla's castells, the
 * favourites pinned on top. Tapping one opens its grid; a long press drags it within its
 * section; its menu pins, renames, duplicates or deletes it, with a snackbar to undo.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ComparatorScenarioList(model: ComparatorViewModel, onOpen: (String) -> Unit) {
    val state by model.state.collectAsState()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var renamingId by rememberSaveable { mutableStateOf<String?>(null) }
    val listState = rememberLazyListState()
    val haptics = LocalHapticFeedback.current
    val reorder = remember(listState) { ScenarioReorder(listState) }
    SideEffect {
        reorder.onMove = model::moveScenario
        reorder.favoriteIds = state.favorites.map { it.id }
        reorder.otherIds = state.others.map { it.id }
    }

    fun delete(scenario: ComparatorScenario) {
        val deleted = model.delete(scenario.id) ?: return
        scope.launch {
            snackbarHostState.currentSnackbarData?.dismiss()
            val result = snackbarHostState.showSnackbar(
                message = "S'ha eliminat l'escenari",
                actionLabel = "Desfés",
                duration = SnackbarDuration.Long,
            )
            if (result == SnackbarResult.ActionPerformed) model.restore(deleted)
        }
    }

    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            TopAppBar(title = { Text("Comparador") }, scrollBehavior = scrollBehavior)
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { onOpen(model.addEmptyScenario().id) },
                icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                text = { Text("Escenari nou") },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        LazyColumn(
            state = listState,
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .pointerInput(reorder, haptics) { with(reorder) { detectReorder(haptics) } },
            // Room for the button over the last row.
            contentPadding = PaddingValues(bottom = 96.dp),
        ) {
            val canDelete = state.scenarios.size > 1
            for (favorites in listOf(true, false)) {
                val scenarios = if (favorites) state.favorites else state.others
                if (favorites && scenarios.isEmpty()) continue
                if (state.favorites.isNotEmpty()) {
                    item(key = if (favorites) FAVORITES_HEADER else OTHERS_HEADER, contentType = "header") {
                        SectionHeader(if (favorites) "Favorits" else "Escenaris", Modifier.animateItem())
                    }
                }
                items(scenarios, key = { it.id }, contentType = { "scenario" }) { scenario ->
                    val isDragged = reorder.draggedId == scenario.id
                    val position = scenarios.indexOf(scenario)
                    ScenarioRow(
                        model = model,
                        scenario = scenario,
                        isDragged = isDragged,
                        canDelete = canDelete,
                        canMoveUp = position > 0,
                        canMoveDown = position < scenarios.lastIndex,
                        // A long press that starts a drag ends with the finger up on the row.
                        onOpen = { if (reorder.draggedId == null) onOpen(scenario.id) },
                        onRename = { renamingId = scenario.id },
                        onDelete = { delete(scenario) },
                        onMove = { by -> model.moveScenario(favorites, position, position + by) },
                        modifier = Modifier
                            .then(
                                if (isDragged) {
                                    Modifier
                                        .zIndex(1f)
                                        .graphicsLayer { translationY = reorder.draggedTranslation() }
                                } else {
                                    Modifier.animateItem()
                                },
                            )
                            .padding(horizontal = 16.dp, vertical = 4.dp),
                    )
                }
            }
            item(key = "footer", contentType = "footer") {
                SectionFooter(
                    text = "Mantén premut un escenari per moure'l. Duplica'n un per provar què passa si una colla fa un altre castell.",
                    modifier = Modifier
                        .animateItem()
                        .padding(top = 8.dp),
                )
            }
        }
    }

    renamingId?.let { id ->
        state.scenarios.firstOrNull { it.id == id }?.let { scenario ->
            ScenarioRenameDialog(
                initialName = scenario.name.orEmpty(),
                placeholder = model.rules.summary(scenario).title,
                onSave = { name ->
                    model.rename(id, name)
                    renamingId = null
                },
                onDismiss = { renamingId = null },
            )
        }
    }
}

@Composable
private fun ScenarioRow(
    model: ComparatorViewModel,
    scenario: ComparatorScenario,
    isDragged: Boolean,
    canDelete: Boolean,
    canMoveUp: Boolean,
    canMoveDown: Boolean,
    onOpen: () -> Unit,
    onRename: () -> Unit,
    onDelete: () -> Unit,
    onMove: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val summary = remember(scenario) { model.rules.summary(scenario) }
    var showsMenu by remember { mutableStateOf(false) }
    val favoriteLabel = if (scenario.isFavorite) "Treu de favorits" else "Afegeix a favorits"
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceContainerHigh,
        shadowElevation = if (isDragged) 8.dp else 0.dp,
    ) {
        Row(
            modifier = Modifier
                .clickable(onClickLabel = "Obre l'escenari", onClick = onOpen)
                .semantics {
                    customActions = buildList {
                        add(CustomAccessibilityAction(favoriteLabel) { model.toggleFavorite(scenario.id); true })
                        add(CustomAccessibilityAction("Canvia el nom") { onRename(); true })
                        add(CustomAccessibilityAction("Duplica") { model.duplicate(scenario.id); true })
                        if (canMoveUp) add(CustomAccessibilityAction("Mou amunt") { onMove(-1); true })
                        if (canMoveDown) add(CustomAccessibilityAction("Mou avall") { onMove(1); true })
                        if (canDelete) add(CustomAccessibilityAction("Elimina") { onDelete(); true })
                    }
                }
                .padding(start = 16.dp, top = 12.dp, bottom = 12.dp, end = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (scenario.isFavorite) {
                        Icon(
                            Icons.Filled.Star,
                            contentDescription = "Favorit",
                            tint = CastellsTheme.colors.star,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                    Text(
                        text = scenario.name ?: summary.title,
                        style = MaterialTheme.typography.titleMedium.merge(TabularNumbers),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                if (scenario.name != null) {
                    Text(
                        text = summary.title,
                        style = MaterialTheme.typography.labelLarge.merge(TabularNumbers),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                for (line in summary.lines) {
                    Text(
                        text = line,
                        style = MaterialTheme.typography.bodySmall.merge(CastellNotation).copy(fontWeight = null),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            Box {
                IconButton(onClick = { showsMenu = true }) {
                    Icon(Icons.Filled.MoreVert, contentDescription = "Opcions de l'escenari")
                }
                DropdownMenu(expanded = showsMenu, onDismissRequest = { showsMenu = false }) {
                    DropdownMenuItem(
                        text = { Text(favoriteLabel) },
                        leadingIcon = {
                            Icon(if (scenario.isFavorite) Icons.Filled.Star else Icons.Outlined.StarBorder, contentDescription = null)
                        },
                        onClick = {
                            showsMenu = false
                            model.toggleFavorite(scenario.id)
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("Canvia el nom") },
                        leadingIcon = { Icon(Icons.Outlined.Edit, contentDescription = null) },
                        onClick = {
                            showsMenu = false
                            onRename()
                        },
                    )
                    DropdownMenuItem(
                        text = { Text("Duplica") },
                        leadingIcon = { Icon(Icons.Outlined.ContentCopy, contentDescription = null) },
                        onClick = {
                            showsMenu = false
                            model.duplicate(scenario.id)
                        },
                    )
                    if (canDelete) {
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
        }
    }
}

/**
 * Dragging a scenario after a long press, anywhere on the list. The row follows the finger and
 * takes the place of the row of its section whose middle it passes; the model moves it at once,
 * so the rest slide out of its way.
 */
private class ScenarioReorder(private val listState: LazyListState) {
    var onMove: (favorites: Boolean, from: Int, to: Int) -> Unit = { _, _, _ -> }
    var favoriteIds: List<String> = emptyList()
    var otherIds: List<String> = emptyList()

    var draggedId by mutableStateOf<String?>(null)
        private set
    private var initialOffset by mutableFloatStateOf(0f)
    private var delta by mutableFloatStateOf(0f)

    private val draggedItem get() = listState.layoutInfo.visibleItemsInfo.firstOrNull { it.key == draggedId }

    /** Where the row is drawn relative to where the list lays it out. */
    fun draggedTranslation(): Float = draggedItem?.let { initialOffset + delta - it.offset } ?: 0f

    suspend fun PointerInputScope.detectReorder(haptics: HapticFeedback) {
        detectDragGesturesAfterLongPress(
            onDragStart = { start ->
                val item = listState.layoutInfo.visibleItemsInfo.firstOrNull { item ->
                    start.y.toInt() in item.offset..(item.offset + item.size)
                } ?: return@detectDragGesturesAfterLongPress
                val id = item.key as? String ?: return@detectDragGesturesAfterLongPress
                if (id !in favoriteIds && id !in otherIds) return@detectDragGesturesAfterLongPress
                draggedId = id
                initialOffset = item.offset.toFloat()
                delta = 0f
                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
            },
            onDrag = { change, amount ->
                if (draggedId == null) return@detectDragGesturesAfterLongPress
                change.consume()
                delta += amount.y
                moveIfOverAnother()
            },
            onDragEnd = ::stop,
            onDragCancel = ::stop,
        )
    }

    private fun moveIfOverAnother() {
        val dragged = draggedItem ?: return
        val id = draggedId ?: return
        val favorites = id in favoriteIds
        val group = if (favorites) favoriteIds else otherIds
        val middle = (initialOffset + delta + dragged.size / 2f).toInt()
        val target = listState.layoutInfo.visibleItemsInfo.firstOrNull { item ->
            item.key != id && item.key in group && middle in item.offset..(item.offset + item.size)
        } ?: return
        onMove(favorites, group.indexOf(id), group.indexOf(target.key))
    }

    private fun stop() {
        draggedId = null
        delta = 0f
    }
}
