package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.outlined.ContentCopy
import androidx.compose.material.icons.outlined.DeleteSweep
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.PersonAdd
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorCell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import kotlinx.coroutines.launch

/** The collaId the colla picker receives to add a new column instead of changing one. */
private const val NEW_COLLA = ""

private val CellSaver = Saver<ComparatorCell?, String>(
    save = { cell -> cell?.let { "${it.round}|${it.collaId}" } },
    restore = { saved ->
        val (round, collaId) = saved.split('|', limit = 2)
        ComparatorCell(collaId, round.toInt())
    },
)

/**
 * The grid of the open scenario: the header with the totals over the rounds of each colla. The
 * header and the grid scroll sideways together once the columns no longer fit.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ComparatorScenarioScreen(model: ComparatorViewModel, onBack: () -> Unit) {
    val state by model.state.collectAsState()
    val scenario = state.current
    val ranking = remember(scenario) { model.rules.ranking(scenario.colles) }
    var selection by rememberSaveable(stateSaver = CellSaver) { mutableStateOf<ComparatorCell?>(null) }
    var outcomeTarget by rememberSaveable(stateSaver = CellSaver) { mutableStateOf<ComparatorCell?>(null) }
    // The colla whose column the picker changes, or NEW_COLLA for a new column.
    var collaTarget by rememberSaveable { mutableStateOf<String?>(null) }
    var isRenaming by rememberSaveable { mutableStateOf(false) }
    var showsMenu by remember { mutableStateOf(false) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    fun clearRounds() {
        val before = model.clearCurrent()
        selection = null
        scope.launch {
            snackbarHostState.currentSnackbarData?.dismiss()
            val result = snackbarHostState.showSnackbar(message = "S'han buidat les rondes", actionLabel = "Desfés")
            if (result == SnackbarResult.ActionPerformed) model.restore(before)
        }
    }

    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            TopAppBar(
                title = { Text(scenario.name ?: "Escenari", maxLines = 1, overflow = TextOverflow.Ellipsis) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Torna als escenaris")
                    }
                },
                actions = {
                    Box {
                        IconButton(onClick = { showsMenu = true }) {
                            Icon(Icons.Filled.MoreVert, contentDescription = "Més opcions")
                        }
                        DropdownMenu(expanded = showsMenu, onDismissRequest = { showsMenu = false }) {
                            DropdownMenuItem(
                                text = { Text("Canvia el nom") },
                                leadingIcon = { Icon(Icons.Outlined.Edit, contentDescription = null) },
                                onClick = {
                                    showsMenu = false
                                    isRenaming = true
                                },
                            )
                            DropdownMenuItem(
                                text = { Text("Duplica l'escenari") },
                                leadingIcon = { Icon(Icons.Outlined.ContentCopy, contentDescription = null) },
                                onClick = {
                                    showsMenu = false
                                    selection = null
                                    model.duplicateCurrent()
                                },
                            )
                            if (scenario.colles.size < ComparatorViewModel.MAX_COLLES) {
                                DropdownMenuItem(
                                    text = { Text("Afegeix una colla") },
                                    leadingIcon = { Icon(Icons.Outlined.PersonAdd, contentDescription = null) },
                                    onClick = {
                                        showsMenu = false
                                        collaTarget = NEW_COLLA
                                    },
                                )
                            }
                            HorizontalDivider()
                            DropdownMenuItem(
                                text = { Text("Buida les rondes") },
                                leadingIcon = { Icon(Icons.Outlined.DeleteSweep, contentDescription = null) },
                                colors = MenuDefaults.itemColors(
                                    textColor = MaterialTheme.colorScheme.error,
                                    leadingIconColor = MaterialTheme.colorScheme.error,
                                ),
                                onClick = {
                                    showsMenu = false
                                    clearRounds()
                                },
                            )
                        }
                    }
                },
                scrollBehavior = scrollBehavior,
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        BoxWithConstraints(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
        ) {
            val columnWidth = ComparatorLayout.columnWidth(maxWidth, scenario.colles.size)
            // One state for both, so that the header's columns follow the grid's.
            val horizontalScroll = rememberScrollState()
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(top = 4.dp),
            ) {
                ComparatorHeader(
                    model = model,
                    scenario = scenario,
                    ranking = ranking,
                    columnWidth = columnWidth,
                    horizontalScroll = horizontalScroll,
                    onEditColla = { collaTarget = it ?: NEW_COLLA },
                    modifier = Modifier.padding(horizontal = ComparatorLayout.HorizontalPadding),
                )
                Spacer(Modifier.height(12.dp))
                ComparatorGrid(
                    model = model,
                    scenario = scenario,
                    ranking = ranking,
                    columnWidth = columnWidth,
                    selection = selection,
                    onTap = { selection = it },
                    onTapOutcome = { outcomeTarget = it },
                    modifier = Modifier
                        .horizontalScroll(horizontalScroll)
                        .padding(horizontal = ComparatorLayout.HorizontalPadding),
                )
                Text(
                    text = "Compten les 3 millors construccions, amb un màxim de 2 carregats. Les penalitzacions només desempaten.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 16.dp),
                )
            }
        }
    }

    // A cell of a colla that is gone has nothing to edit.
    val collaIds = scenario.colles.map { it.id }
    selection?.takeIf { it.collaId in collaIds }?.let { cell ->
        ComparatorCastellSheet(model = model, cell = cell, onDismiss = { selection = null })
    }
    outcomeTarget?.takeIf { it.collaId in collaIds }?.let { cell ->
        ComparatorOutcomeSheet(model = model, cell = cell, onDismiss = { outcomeTarget = null })
    }
    collaTarget?.let { target ->
        val isNew = target == NEW_COLLA
        ComparatorCollaPicker(
            title = if (isNew) "Afegeix una colla" else "Canvia la colla",
            takenNames = scenario.colles.map { it.name }.toSet(),
            onPick = { known ->
                if (isNew) model.addColla(known) else model.replaceColla(target, known)
                collaTarget = null
            },
            onDismiss = { collaTarget = null },
        )
    }
    if (isRenaming) {
        ScenarioRenameDialog(
            initialName = scenario.name.orEmpty(),
            placeholder = remember(scenario) { model.rules.summary(scenario).title },
            onSave = { name ->
                model.rename(scenario.id, name)
                isRenaming = false
            },
            onDismiss = { isRenaming = false },
        )
    }
}
