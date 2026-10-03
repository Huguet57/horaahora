package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.onClick
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellNotation
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTableCastell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorCell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorOutcome
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorRestriction
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.PlannedCastell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.formattedPoints
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

private val LadderRowHeight = 48.dp

/**
 * Castells without manilles that have never been done, each with the one with folre and
 * manilles it is easily mistaken for.
 */
private val UnlikelyCastells = mapOf("3de10sm" to "3de10fm", "4de10sm" to "4de10fm")

/**
 * The bottom sheet for a cell, in two steps. First every castell by points, opened on the
 * cell's castell or, for an empty cell, near what the colles did; the ones the colla may not
 * try are disabled and say why. Then the result of the picked castell, which puts it in the
 * cell and closes the sheet.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ComparatorCastellSheet(model: ComparatorViewModel, cell: ComparatorCell, onDismiss: () -> Unit) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    val state by model.state.collectAsState()
    val colla = state.current.colles.firstOrNull { it.id == cell.collaId }
    val castell = colla?.rounds?.getOrNull(cell.round)
    // The castell picked in the first step, whose result the second step asks for.
    var pickedNotation by rememberSaveable(cell) { mutableStateOf<String?>(null) }
    // A castell without manilles, tapped in the first step and waiting to be confirmed.
    var unlikelyNotation by rememberSaveable(cell) { mutableStateOf<String?>(null) }
    val reduceMotion = LocalReduceMotion.current

    fun close() {
        scope.launch { sheetState.hide() }.invokeOnCompletion { onDismiss() }
    }

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        if (colla == null) return@ModalBottomSheet
        Column(
            modifier = Modifier
                .fillMaxWidth()
                // One height for both steps, so the sheet does not jump between them.
                .fillMaxHeight(0.6f)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SheetHeader(
                collaName = colla.name,
                round = cell.round,
                pickedNotation = pickedNotation,
                canClear = castell != null,
                onBack = { pickedNotation = null },
                onClear = {
                    model.set(null, cell)
                    close()
                },
            )
            AnimatedContent(
                targetState = pickedNotation,
                transitionSpec = {
                    when {
                        reduceMotion -> EnterTransition.None togetherWith ExitTransition.None
                        targetState != null -> slideInHorizontally { it / 3 } + fadeIn() togetherWith fadeOut()
                        else -> slideInHorizontally { -it / 3 } + fadeIn() togetherWith fadeOut()
                    }
                },
                modifier = Modifier.weight(1f),
                label = "castell-step",
            ) { picked ->
                if (picked == null) {
                    CastellLadder(
                        castells = remember(model) { model.rules.ladder(ComparatorOutcome.UNLOADED).asReversed() },
                        anchor = remember(cell) { model.anchor(cell) },
                        current = castell?.notation,
                        restriction = { notation -> model.rules.restriction(notation, cell.round, colla) },
                        onPick = { notation ->
                            if (notation in UnlikelyCastells && notation != castell?.notation) {
                                unlikelyNotation = notation
                            } else {
                                pickedNotation = notation
                            }
                        },
                    )
                } else {
                    Column(modifier = Modifier.fillMaxSize()) {
                        ComparatorOutcomeGrid(current = castell?.takeIf { it.notation == picked }?.outcome) { outcome ->
                            model.set(PlannedCastell(picked, outcome), cell)
                            close()
                        }
                    }
                }
            }
        }
    }

    unlikelyNotation?.let { notation ->
        UnlikelyCastellDialog(
            notation = notation,
            alternative = UnlikelyCastells[notation],
            onPick = {
                unlikelyNotation = null
                pickedNotation = it
            },
            onDismiss = { unlikelyNotation = null },
        )
    }
}

/** Asks whether a castell that has never been done is meant, or the [alternative] it looks like. */
@Composable
private fun UnlikelyCastellDialog(
    notation: String,
    alternative: String?,
    onPick: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("$notation sense manilles?") },
        text = { Text("No s'ha fet mai.") },
        confirmButton = {
            Row {
                if (alternative != null) {
                    TextButton(onClick = { onPick(alternative) }) { Text("No, $alternative") }
                }
                TextButton(onClick = { onPick(notation) }) { Text("Sí, $notation") }
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel·la") } },
    )
}

@Composable
private fun SheetHeader(
    collaName: String,
    round: Int,
    pickedNotation: String?,
    canClear: Boolean,
    onBack: () -> Unit,
    onClear: () -> Unit,
) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        if (pickedNotation != null) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Torna als castells")
            }
        }
        Column(modifier = Modifier.weight(1f).padding(start = if (pickedNotation == null) 8.dp else 0.dp)) {
            Text(
                text = collaName,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = listOfNotNull("Ronda ${round + 1}", pickedNotation).joinToString(" · "),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
            )
        }
        OutlinedButton(
            onClick = onClear,
            enabled = canClear,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
            contentPadding = ButtonDefaults.ButtonWithIconContentPadding,
        ) {
            Icon(Icons.Outlined.Delete, contentDescription = null, modifier = Modifier.padding(end = 8.dp))
            Text("Buida")
        }
    }
}

/** Every castell of the table from the most points down, opened with [anchor] in the middle. */
@Composable
private fun CastellLadder(
    castells: List<ScoreTableCastell>,
    anchor: String,
    current: String?,
    restriction: (String) -> ComparatorRestriction?,
    onPick: (String) -> Unit,
) {
    val listState = rememberLazyListState()
    val rowHeight = with(LocalDensity.current) { LadderRowHeight.roundToPx() }
    LaunchedEffect(anchor) {
        val index = castells.indexOfFirst { it.notation == anchor }.coerceAtLeast(0)
        val viewport = snapshotFlow { listState.layoutInfo.viewportSize.height }.first { it > 0 }
        // Every row is as tall, so the scroll that centres it follows from its index.
        val target = (index * rowHeight - (viewport - rowHeight) / 2).coerceAtLeast(0)
        listState.scrollToItem(target / rowHeight, scrollOffset = target % rowHeight)
    }
    LazyColumn(state = listState, contentPadding = PaddingValues(bottom = 16.dp)) {
        items(castells, key = { it.notation }) { castell ->
            LadderRow(
                castell = castell,
                isCurrent = castell.notation == current,
                restriction = restriction(castell.notation),
                onClick = { onPick(castell.notation) },
            )
        }
    }
}

@Composable
private fun LadderRow(castell: ScoreTableCastell, isCurrent: Boolean, restriction: ComparatorRestriction?, onClick: () -> Unit) {
    val isDisabled = restriction != null && !isCurrent
    val disabledColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    val points = formattedPoints(castell.unloaded)
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(LadderRowHeight)
            .clip(RoundedCornerShape(12.dp))
            .background(if (isCurrent) MaterialTheme.colorScheme.secondaryContainer else Color.Transparent)
            .clickable(enabled = !isDisabled, onClick = onClick)
            .clearAndSetSemantics {
                contentDescription = listOfNotNull(castell.name, "$points punts", restriction?.label).joinToString(", ")
                role = Role.Button
                selected = isCurrent
                if (isDisabled) disabled() else onClick { onClick(); true }
            }
            .padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = castell.notation,
            style = MaterialTheme.typography.bodyLarge.merge(CastellNotation)
                .copy(fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal),
            color = if (isDisabled) disabledColor else MaterialTheme.colorScheme.onSurface,
        )
        if (restriction != null) {
            Text(
                text = restriction.label,
                style = MaterialTheme.typography.labelSmall,
                color = if (isDisabled) disabledColor else CastellsTheme.colors.warning,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f, fill = false),
            )
        }
        Spacer(Modifier.weight(1f))
        Text(
            text = points,
            style = MaterialTheme.typography.bodyLarge.merge(TabularNumbers),
            color = when {
                isDisabled -> disabledColor
                isCurrent -> MaterialTheme.colorScheme.onSurface
                else -> MaterialTheme.colorScheme.onSurfaceVariant
            },
        )
    }
}

/** The result of a cell's castell, opened from its D/C badge. Picking one sets it and closes. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ComparatorOutcomeSheet(model: ComparatorViewModel, cell: ComparatorCell, onDismiss: () -> Unit) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    val state by model.state.collectAsState()
    val colla = state.current.colles.firstOrNull { it.id == cell.collaId }
    val castell = colla?.rounds?.getOrNull(cell.round)

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        if (colla == null || castell == null) return@ModalBottomSheet
        Column(
            modifier = Modifier.padding(start = 16.dp, end = 16.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(
                text = "${colla.name} · Ronda ${cell.round + 1} · ${castell.notation}",
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(horizontal = 8.dp),
            )
            ComparatorOutcomeGrid(current = castell.outcome) { outcome ->
                model.setOutcome(outcome, cell)
                scope.launch { sheetState.hide() }.invokeOnCompletion { onDismiss() }
            }
        }
    }
}

/** Descarregat, carregat, intent and intent desmuntat as four big buttons, the current one filled. */
@Composable
internal fun ComparatorOutcomeGrid(current: ComparatorOutcome?, onPick: (ComparatorOutcome) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        for (pair in ComparatorOutcome.entries.chunked(2)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                for (outcome in pair) {
                    OutcomeOption(
                        outcome = outcome,
                        isCurrent = outcome == current,
                        onClick = { onPick(outcome) },
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun OutcomeOption(outcome: ComparatorOutcome, isCurrent: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val color = outcome.color()
    Surface(
        onClick = onClick,
        modifier = modifier
            .heightIn(min = 88.dp)
            .semantics {
                selected = isCurrent
                if (isCurrent) stateDescription = "Resultat actual"
            },
        shape = RoundedCornerShape(16.dp),
        color = if (isCurrent) color else color.copy(alpha = 0.14f),
        contentColor = if (isCurrent) contentColorOver(color) else color,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(outcome.shortLabel, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black)
            Text(outcome.label, style = MaterialTheme.typography.labelLarge)
        }
    }
}
