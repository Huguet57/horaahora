package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.max
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorOutcome
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel

/** The widths the header and the grid share, so that their columns line up. */
internal object ComparatorLayout {
    val HorizontalPadding = 12.dp
    val Spacing = 6.dp

    /** The round labels on the left of the grid, which the header leaves free too. */
    val GutterWidth = 30.dp

    /** The slot after the last colla where the next one would go, empty in the grid. */
    val AddColumnWidth = 48.dp

    /** Narrower columns cramp a castell and its result; past it the columns scroll sideways. */
    private val MinColumnWidth = 116.dp

    /** The colla columns share what the screen leaves them, down to [MinColumnWidth]. */
    fun columnWidth(viewport: Dp, colles: Int): Dp {
        val hasAddSlot = colles < ComparatorViewModel.MAX_COLLES
        val gaps = colles + if (hasAddSlot) 1 else 0
        val fixed = HorizontalPadding * 2 + GutterWidth + Spacing * gaps + if (hasAddSlot) AddColumnWidth else 0.dp
        return max(MinColumnWidth, (viewport - fixed) / maxOf(colles, 1))
    }
}

/** Descarregat in green, carregat in the accent, and attempts in grey. */
@Composable
@ReadOnlyComposable
internal fun ComparatorOutcome.color(): Color = when (this) {
    ComparatorOutcome.UNLOADED -> CastellsTheme.colors.success
    ComparatorOutcome.LOADED -> MaterialTheme.colorScheme.primary
    ComparatorOutcome.ATTEMPT, ComparatorOutcome.DISMANTLED_ATTEMPT -> MaterialTheme.colorScheme.outline
}

/** Text over a filled [color]: the dark theme's colors are light, so they take dark text. */
internal fun contentColorOver(color: Color): Color = if (color.luminance() > 0.4f) Color(0xFF1F1A1A) else Color.White

/** "D", "C", "I" or "ID" on the outcome's color. */
@Composable
internal fun ComparatorOutcomeBadge(outcome: ComparatorOutcome, isCompact: Boolean, modifier: Modifier = Modifier) {
    val color = outcome.color()
    Text(
        text = outcome.shortLabel,
        style = if (isCompact) MaterialTheme.typography.labelSmall else MaterialTheme.typography.labelMedium,
        fontWeight = FontWeight.Black,
        color = contentColorOver(color),
        textAlign = TextAlign.Center,
        modifier = modifier
            .background(color, RoundedCornerShape(5.dp))
            .defaultMinSize(minWidth = if (isCompact) 18.dp else 22.dp)
            .padding(horizontal = if (isCompact) 4.dp else 6.dp, vertical = 1.dp),
    )
}

/** A dashed outline for a place still to fill: an empty round, or a colla to add. */
internal fun Modifier.dashedBorder(color: Color, cornerRadius: Dp): Modifier = drawBehind {
    val stroke = 1.dp.toPx()
    drawRoundRect(
        color = color,
        topLeft = Offset(stroke / 2, stroke / 2),
        size = Size(size.width - stroke, size.height - stroke),
        cornerRadius = CornerRadius(cornerRadius.toPx()),
        style = Stroke(width = stroke, pathEffect = PathEffect.dashPathEffect(floatArrayOf(4.dp.toPx(), 3.dp.toPx()))),
    )
}
