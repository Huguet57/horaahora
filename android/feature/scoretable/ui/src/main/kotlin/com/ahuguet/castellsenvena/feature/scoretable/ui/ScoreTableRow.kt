package com.ahuguet.castellsenvena.feature.scoretable.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.State
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTableCastell

private val BarHeight = 6.dp

/** Wide enough for «Descarregat», and it grows with the font size. */
@Composable
private fun pointsColumnWidth(): Dp = with(LocalDensity.current) { 84.sp.toDp() }

/** The solid part of a bar reaches the carregat points; the whole bar, the descarregat ones. */
@Composable
private fun loadedBarColor(): Color = MaterialTheme.colorScheme.primary

@Composable
private fun unloadedBarColor(): Color = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)

internal sealed interface ScoreTableHighlight {
    data object None : ScoreTableHighlight

    /** The tapped castell: its carregat is the value to beat. */
    data object Selected : ScoreTableHighlight

    /** Its descarregat beats the carregat of the tapped castell. */
    data class BeatsSelectedLoaded(val selectedNotation: String) : ScoreTableHighlight
}

@Composable
internal fun ScoreTableSectionHeader(group: Int, modifier: Modifier = Modifier) {
    val width = pointsColumnWidth()
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 6.dp)
            .clearAndSetSemantics {
                heading()
                contentDescription = "Grup $group"
            },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = "Grup $group",
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1f),
        )
        Legend("Carregat", loadedBarColor(), width)
        Legend("Descarregat", unloadedBarColor(), width)
    }
}

@Composable
private fun Legend(title: String, color: Color, width: Dp) {
    Row(
        modifier = Modifier.width(width),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp, Alignment.End),
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(color),
        )
        Text(
            text = title,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            maxLines = 1,
        )
    }
}

@Composable
internal fun ScoreTableRow(
    castell: ScoreTableCastell,
    scale: State<BarScale>,
    highlight: ScoreTableHighlight,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val isSelected = highlight == ScoreTableHighlight.Selected
    val beatsSelection = highlight is ScoreTableHighlight.BeatsSelectedLoaded
    val primary = MaterialTheme.colorScheme.primary
    val loaded = CatalanNumbers.grouped(castell.loaded)
    val unloaded = CatalanNumbers.grouped(castell.unloaded)
    val loadedColor = loadedBarColor()
    val unloadedColor = unloadedBarColor()
    val width = pointsColumnWidth()

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(
                when (highlight) {
                    ScoreTableHighlight.None -> Color.Transparent
                    ScoreTableHighlight.Selected -> primary.copy(alpha = 0.16f)
                    is ScoreTableHighlight.BeatsSelectedLoaded -> primary.copy(alpha = 0.06f)
                },
            )
            .clickable(onClickLabel = "mostrar quins castells de sota guanyen el seu carregat si es descarreguen", onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .clearAndSetSemantics {
                role = Role.Button
                selected = isSelected
                contentDescription = "${castell.name}, ${castell.notation}"
                stateDescription = buildString {
                    append("Carregat, $loaded punts. Descarregat, $unloaded punts.")
                    if (highlight is ScoreTableHighlight.BeatsSelectedLoaded) {
                        append(" El descarregat guanya el carregat del ${highlight.selectedNotation}.")
                    }
                }
            },
    ) {
        Row(
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = castell.notation,
                style = MaterialTheme.typography.bodyLarge.copy(fontFamily = FontFamily.Monospace),
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.weight(1f),
            )
            Points(
                text = loaded,
                color = if (isSelected) primary else MaterialTheme.colorScheme.onSurfaceVariant,
                emphasized = isSelected,
                width = width,
            )
            Points(
                text = unloaded,
                color = if (beatsSelection) primary else MaterialTheme.colorScheme.onSurface,
                emphasized = beatsSelection,
                width = width,
            )
        }
        Spacer(Modifier.height(6.dp))
        // Square ends so that bars compare exactly. The bar reads the scale while
        // drawing, so scrolling redraws it without recomposing the row.
        Spacer(
            modifier = Modifier
                .fillMaxWidth()
                .height(BarHeight)
                .drawBehind {
                    val current = scale.value
                    if (castell.notation !in current.wholeRows) return@drawBehind
                    drawRect(
                        color = unloadedColor,
                        size = Size(size.width * current.axis.fraction(castell.unloaded).toFloat(), size.height),
                    )
                    drawRect(
                        color = loadedColor,
                        size = Size(size.width * current.axis.fraction(castell.loaded).toFloat(), size.height),
                    )
                },
        )
    }
}

@Composable
private fun Points(text: String, color: Color, emphasized: Boolean, width: Dp) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium.copy(fontFeatureSettings = "tnum"),
        fontWeight = if (emphasized) FontWeight.SemiBold else FontWeight.Normal,
        color = color,
        textAlign = TextAlign.End,
        maxLines = 1,
        modifier = Modifier.width(width),
    )
}
