package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellNotation
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorCell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorColla
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorOutcome
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorRestriction
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorScenario
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorStanding
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.PlannedCastell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.RoundScore
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.formattedPoints

private val CellShape = RoundedCornerShape(12.dp)

/**
 * The five rounds down and the colles across. Tapping a cell opens the castell sheet for it,
 * tapping its D/C badge the result sheet, and a long press shows its menu. TalkBack can also
 * step a cell to the next castell up or down.
 */
@Composable
internal fun ComparatorGrid(
    model: ComparatorViewModel,
    scenario: ComparatorScenario,
    ranking: List<ComparatorStanding>,
    columnWidth: Dp,
    selection: ComparatorCell?,
    onTap: (ComparatorCell) -> Unit,
    onTapOutcome: (ComparatorCell) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colles = scenario.colles
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(ComparatorLayout.Spacing)) {
        for (round in 0 until ComparatorColla.ROUND_COUNT) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(ComparatorLayout.Spacing),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "R${round + 1}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.width(ComparatorLayout.GutterWidth),
                )
                for (colla in colles) {
                    key(colla.id) {
                        val cell = ComparatorCell(colla.id, round)
                        val castell = colla.rounds[round]
                        GridCell(
                            model = model,
                            colla = colla,
                            cell = cell,
                            castell = castell,
                            roundScore = ranking.firstOrNull { it.collaId == colla.id }?.score?.rounds?.getOrNull(round),
                            restriction = castell?.let { model.rules.restriction(it.notation, round, colla) },
                            isSelected = selection == cell,
                            isCompact = colles.size > 2,
                            width = columnWidth,
                            onTap = { onTap(cell) },
                            onTapOutcome = { onTapOutcome(cell) },
                        )
                    }
                }
                if (colles.size < ComparatorViewModel.MAX_COLLES) {
                    Spacer(Modifier.width(ComparatorLayout.AddColumnWidth))
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun GridCell(
    model: ComparatorViewModel,
    colla: ComparatorColla,
    cell: ComparatorCell,
    castell: PlannedCastell?,
    roundScore: RoundScore?,
    restriction: ComparatorRestriction?,
    isSelected: Boolean,
    isCompact: Boolean,
    width: Dp,
    onTap: () -> Unit,
    onTapOutcome: () -> Unit,
) {
    var showsMenu by remember { mutableStateOf(false) }
    val outline = MaterialTheme.colorScheme.outlineVariant
    val selectedColor = MaterialTheme.colorScheme.primary
    Box {
        Box(
            modifier = Modifier
                .width(width)
                .heightIn(min = if (isCompact) 56.dp else 64.dp)
                .clip(CellShape)
                .then(
                    if (castell == null) {
                        Modifier.dashedBorder(outline, 12.dp)
                    } else {
                        Modifier.background(MaterialTheme.colorScheme.surfaceContainerHigh)
                    },
                )
                .then(if (isSelected) Modifier.border(2.dp, selectedColor, CellShape) else Modifier)
                .combinedClickable(
                    onClickLabel = if (castell == null) "Tria un castell" else "Canvia el castell",
                    onLongClickLabel = "Més opcions",
                    onLongClick = if (castell != null) ({ showsMenu = true }) else null,
                    onClick = onTap,
                )
                .semantics {
                    contentDescription = "${colla.name}, ronda ${cell.round + 1}"
                    stateDescription = castell?.let { "${it.notation}, ${it.outcome.label}" } ?: "buida"
                    selected = isSelected
                    if (castell != null) {
                        customActions = listOf(
                            CustomAccessibilityAction("Castell següent") { model.step(cell, 1); true },
                            CustomAccessibilityAction("Castell anterior") { model.step(cell, -1); true },
                        )
                    }
                },
            contentAlignment = Alignment.Center,
        ) {
            if (castell == null) {
                EmptyCell(isCompact)
            } else {
                FilledCell(castell, roundScore, restriction, isCompact, onTapOutcome)
            }
        }
        if (castell != null) {
            CellMenu(
                expanded = showsMenu,
                current = castell.outcome,
                onDismiss = { showsMenu = false },
                onOutcome = { model.setOutcome(it, cell) },
                onClear = { model.set(null, cell) },
            )
        }
    }
}

@Composable
private fun EmptyCell(isCompact: Boolean) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        Icon(
            Icons.Filled.Add,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(18.dp),
        )
        if (!isCompact) {
            Text("castell", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun FilledCell(
    castell: PlannedCastell,
    roundScore: RoundScore?,
    restriction: ComparatorRestriction?,
    isCompact: Boolean,
    onTapOutcome: () -> Unit,
) {
    val notCounted = roundScore?.notCountedReason
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (notCounted == null) 1f else 0.5f)
            .padding(start = if (isCompact) 8.dp else 10.dp, end = 4.dp, top = 4.dp, bottom = 8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = castell.notation,
                style = (if (isCompact) MaterialTheme.typography.bodyMedium else MaterialTheme.typography.bodyLarge)
                    .merge(CastellNotation),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f),
            )
            // A bigger target than the badge itself, which is small to tap.
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .clickable(onClickLabel = "Canvia el resultat", role = Role.Button, onClick = onTapOutcome)
                    .semantics { contentDescription = "Resultat: ${castell.outcome.label}" }
                    .padding(6.dp),
            ) {
                ComparatorOutcomeBadge(castell.outcome, isCompact)
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            val secondary = MaterialTheme.colorScheme.onSurfaceVariant
            val style = MaterialTheme.typography.labelSmall
            when {
                restriction != null -> {
                    Icon(
                        Icons.Filled.Warning,
                        contentDescription = if (isCompact) restriction.label else null,
                        tint = CastellsTheme.colors.warning,
                        modifier = Modifier.size(14.dp),
                    )
                    if (!isCompact) {
                        Text(restriction.label, style = style, color = CastellsTheme.colors.warning, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
                notCounted != null -> Text(
                    text = if (isCompact) "no compta" else "no compta · ${notCounted.label}",
                    style = style,
                    color = secondary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                else -> Text(formattedPoints(roundScore?.points ?: 0), style = style.merge(TabularNumbers), color = secondary)
            }
        }
    }
}

/** A long press on a cell: its result, or emptying the round. */
@Composable
private fun CellMenu(
    expanded: Boolean,
    current: ComparatorOutcome,
    onDismiss: () -> Unit,
    onOutcome: (ComparatorOutcome) -> Unit,
    onClear: () -> Unit,
) {
    DropdownMenu(expanded = expanded, onDismissRequest = onDismiss) {
        for (outcome in ComparatorOutcome.entries) {
            DropdownMenuItem(
                text = { Text(outcome.label) },
                leadingIcon = { ComparatorOutcomeBadge(outcome, isCompact = false) },
                trailingIcon = if (outcome == current) ({ Icon(Icons.Filled.Check, contentDescription = "Actual") }) else null,
                onClick = {
                    onDismiss()
                    onOutcome(outcome)
                },
            )
        }
        HorizontalDivider()
        DropdownMenuItem(
            text = { Text("Buida la ronda") },
            leadingIcon = { Icon(Icons.Outlined.Delete, contentDescription = null) },
            colors = MenuDefaults.itemColors(
                textColor = MaterialTheme.colorScheme.error,
                leadingIconColor = MaterialTheme.colorScheme.error,
            ),
            onClick = {
                onDismiss()
                onClear()
            },
        )
    }
}
