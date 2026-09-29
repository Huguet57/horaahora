package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.animation.core.animateIntAsState
import androidx.compose.animation.core.snap
import androidx.compose.animation.core.tween
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Balance
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.outlined.PersonRemove
import androidx.compose.material.icons.outlined.SwapHoriz
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorColla
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorScenario
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorStanding
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.formattedMargin
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.formattedPoints

/**
 * The totals of each colla, its place and gap to the first, and who leads by how much. The
 * columns scroll sideways with the grid's, through the same [horizontalScroll]; the line of who
 * leads stays put. It keeps its height as points come and go, so the grid never jumps.
 */
@Composable
internal fun ComparatorHeader(
    model: ComparatorViewModel,
    scenario: ComparatorScenario,
    ranking: List<ComparatorStanding>,
    columnWidth: Dp,
    horizontalScroll: ScrollState,
    onEditColla: (collaId: String?) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colles = scenario.colles
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceContainerHigh,
    ) {
        Column(modifier = Modifier.padding(vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                modifier = Modifier
                    .horizontalScroll(horizontalScroll)
                    .height(IntrinsicSize.Min),
                horizontalArrangement = Arrangement.spacedBy(ComparatorLayout.Spacing),
            ) {
                // Leaves the round labels' width free, so the columns line up with the grid's.
                Spacer(Modifier.width(ComparatorLayout.GutterWidth))
                for (colla in colles) {
                    CollaColumn(
                        model = model,
                        colla = colla,
                        ranking = ranking,
                        collaCount = colles.size,
                        width = columnWidth,
                        onEditColla = { onEditColla(colla.id) },
                    )
                }
                if (colles.size < ComparatorViewModel.MAX_COLLES) {
                    AddCollaSlot(onClick = { onEditColla(null) })
                }
            }
            if (ranking.size > 1) {
                LeaderLine(
                    scenario = scenario,
                    ranking = ranking,
                    modifier = Modifier.padding(horizontal = 16.dp),
                )
            }
        }
    }
}

@Composable
private fun AddCollaSlot(onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .width(ComparatorLayout.AddColumnWidth)
            .fillMaxHeight()
            .padding(end = 8.dp)
            .clip(RoundedCornerShape(10.dp))
            .dashedBorder(MaterialTheme.colorScheme.outline, 10.dp)
            .clickable(role = Role.Button, onClick = onClick)
            .semantics { contentDescription = "Afegeix una colla" },
        contentAlignment = Alignment.Center,
    ) {
        Icon(Icons.Filled.Add, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun CollaColumn(
    model: ComparatorViewModel,
    colla: ComparatorColla,
    ranking: List<ComparatorStanding>,
    collaCount: Int,
    width: Dp,
    onEditColla: () -> Unit,
) {
    val index = ranking.indexOfFirst { it.collaId == colla.id }
    val position = index + 1
    val score = ranking.getOrNull(index)?.score
    val total = score?.total ?: 0
    val leaderTotal = ranking.firstOrNull()?.score?.total ?: 0
    val isLeader = position == 1 && collaCount > 1 && total > 0
    val isCompact = collaCount > 2
    val reduceMotion = LocalReduceMotion.current
    val shownTotal by animateIntAsState(
        targetValue = total,
        animationSpec = if (reduceMotion) snap() else tween(durationMillis = 350),
        label = "total",
    )
    var showsMenu by remember { mutableStateOf(false) }

    Column(modifier = Modifier.width(width)) {
        Box {
            Row(
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .clickable(onClickLabel = "Opcions de la colla") { showsMenu = true }
                    .padding(vertical = 2.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                if (collaCount > 1) PositionBadge(position, isLeader)
                Text(
                    text = if (isCompact) colla.shortName else colla.name,
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f, fill = false),
                )
                Icon(
                    Icons.Filled.ArrowDropDown,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(18.dp),
                )
            }
            CollaMenu(
                expanded = showsMenu,
                colla = colla,
                canRemove = collaCount > 1,
                onDismiss = { showsMenu = false },
                onChange = onEditColla,
                onPenalty = { model.changePenalties(colla.id, it) },
                onRemove = { model.removeColla(colla.id) },
            )
        }
        Text(
            text = formattedPoints(shownTotal),
            style = (if (isCompact) MaterialTheme.typography.headlineSmall else MaterialTheme.typography.headlineMedium)
                .merge(TabularNumbers),
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            softWrap = false,
            modifier = Modifier.semantics { contentDescription = "${formattedPoints(total)} punts" },
        )
        // Always there, so that the header keeps its height as points come and go.
        if (collaCount > 1) {
            Text(
                text = gap(position, total, leaderTotal, score?.penalties ?: 0),
                style = MaterialTheme.typography.bodySmall.merge(TabularNumbers),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun PositionBadge(position: Int, isLeader: Boolean) {
    Box(
        modifier = Modifier
            .size(18.dp)
            .background(
                if (isLeader) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceContainerHighest,
                CircleShape,
            ),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = "$position",
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = if (isLeader) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun CollaMenu(
    expanded: Boolean,
    colla: ComparatorColla,
    canRemove: Boolean,
    onDismiss: () -> Unit,
    onChange: () -> Unit,
    onPenalty: (Int) -> Unit,
    onRemove: () -> Unit,
) {
    DropdownMenu(expanded = expanded, onDismissRequest = onDismiss) {
        DropdownMenuItem(
            text = { Text("Canvia la colla…") },
            leadingIcon = { Icon(Icons.Outlined.SwapHoriz, contentDescription = null) },
            onClick = {
                onDismiss()
                onChange()
            },
        )
        DropdownMenuItem(
            text = { Text("Afegeix una penalització") },
            leadingIcon = { Icon(Icons.Filled.Add, contentDescription = null) },
            onClick = {
                onDismiss()
                onPenalty(1)
            },
        )
        if (colla.penalties > 0) {
            DropdownMenuItem(
                text = { Text("Treu una penalització") },
                leadingIcon = { Icon(Icons.Filled.Remove, contentDescription = null) },
                onClick = {
                    onDismiss()
                    onPenalty(-1)
                },
            )
        }
        if (canRemove) {
            HorizontalDivider()
            DropdownMenuItem(
                text = { Text("Treu la colla") },
                leadingIcon = { Icon(Icons.Outlined.PersonRemove, contentDescription = null) },
                colors = MenuDefaults.itemColors(
                    textColor = MaterialTheme.colorScheme.error,
                    leadingIconColor = MaterialTheme.colorScheme.error,
                ),
                onClick = {
                    onDismiss()
                    onRemove()
                },
            )
        }
    }
}

/**
 * "−600", or "—" for the first and while nobody scores, with the penalties that only break
 * ties after it.
 */
private fun gap(position: Int, total: Int, leaderTotal: Int, penalties: Int): String {
    val gap = if (position == 1 || leaderTotal == 0) "—" else formattedMargin(total - leaderTotal)
    return if (penalties > 0) "$gap · $penalties pen." else gap
}

/** Who leads and by how much, or how a tie breaks; always one line. */
@Composable
private fun LeaderLine(scenario: ComparatorScenario, ranking: List<ComparatorStanding>, modifier: Modifier = Modifier) {
    val first = ranking.first()
    val firstColla = scenario.colles.firstOrNull { it.id == first.collaId }
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
    ) {
        if (first.score.total > 0 && firstColla != null) {
            val margin = first.score.total - ranking[1].score.total
            val isTie = margin == 0
            Icon(
                if (isTie) Icons.Filled.Balance else Icons.Filled.EmojiEvents,
                contentDescription = null,
                tint = if (isTie) CastellsTheme.colors.warning else CastellsTheme.colors.star,
                modifier = Modifier.size(20.dp),
            )
            Text(
                text = if (isTie) tieText(firstColla.name, first.tieBreak) else "${firstColla.name} guanya per ${formattedMargin(margin)}",
                style = MaterialTheme.typography.bodyMedium.merge(TabularNumbers),
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        } else {
            Text(
                text = "Encara no hi ha castells",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
            )
        }
    }
}

private fun tieText(winner: String, tieBreak: ComparatorStanding.TieBreak?): String = when (tieBreak) {
    ComparatorStanding.TieBreak.PENALTIES -> "Empat · guanya $winner per menys penalitzacions"
    ComparatorStanding.TieBreak.BEST_CASTELL -> "Empat · guanya $winner pel millor castell"
    ComparatorStanding.TieBreak.SECOND_CASTELL -> "Empat · guanya $winner pel segon castell"
    null -> "Empat total"
}
