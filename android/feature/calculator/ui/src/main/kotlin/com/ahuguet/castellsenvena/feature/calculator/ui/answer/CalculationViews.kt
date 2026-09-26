package com.ahuguet.castellsenvena.feature.calculator.ui.answer

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DragHandle
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.FormatListNumbered
import androidx.compose.material.icons.filled.Functions
import androidx.compose.material.icons.outlined.TableChart
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellNotation
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.calculator.presentation.ComparisonPresentation
import com.ahuguet.castellsenvena.feature.calculator.presentation.PerformanceSummaryPresentation
import com.ahuguet.castellsenvena.feature.calculator.presentation.ScorePresentation

/*
 * The structured answers of the calculator: a comparison of performances, a
 * slice of the score table and the castells of one performance.
 */

private val cellStyle: TextStyle @Composable get() = MaterialTheme.typography.bodySmall
private val detailStyle: TextStyle @Composable get() = MaterialTheme.typography.labelSmall
private val notationStyle: TextStyle @Composable get() = MaterialTheme.typography.bodySmall.merge(CastellNotation)
private val tableBackground: Color @Composable get() = LocalContentColor.current.copy(alpha = 0.045f)

@Composable
internal fun ComparisonTable(presentation: ComparisonPresentation) {
    Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
        SectionLabel(Icons.Outlined.TableChart, "Comparativa")
        TableSurface {
            val header = TableRow.Cells(
                listOf<@Composable () -> Unit>({ Text("Castell", style = cellStyle, color = CastellsTheme.colors.secondaryText) }) +
                    presentation.columns.map { column ->
                        {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                if (column.isWinner) {
                                    Icon(
                                        imageVector = Icons.Filled.EmojiEvents,
                                        contentDescription = "Guanyadora",
                                        tint = CastellsTheme.colors.star,
                                        modifier = Modifier.size(16.dp),
                                    )
                                    Spacer(Modifier.size(4.dp))
                                }
                                Text(column.label, style = cellStyle, fontWeight = FontWeight.SemiBold, maxLines = 1)
                            }
                        }
                    },
            )
            val castellRows = (0 until presentation.maximumCastellCount).map { index ->
                TableRow.Cells(
                    listOf<@Composable () -> Unit>({
                        Text("${index + 1}", style = detailStyle, color = CastellsTheme.colors.tertiaryText)
                    }) + presentation.columns.map { column -> { ComparisonCastellCell(column.castells.getOrNull(index)) } },
                )
            }
            val total = TableRow.Cells(
                listOf<@Composable () -> Unit>({ Text("Total", style = cellStyle, fontWeight = FontWeight.SemiBold) }) +
                    presentation.columns.map { column ->
                        { Text(CatalanNumbers.grouped(column.total), style = cellStyle.merge(TabularNumbers), fontWeight = FontWeight.Bold) }
                    },
            )
            ScoreTable(
                rows = listOf(header, TableRow.Divider) + castellRows + listOf(TableRow.Divider, total),
                columnCount = presentation.columns.size + 1,
                minColumnWidths = listOf(0.dp) + presentation.columns.map { 112.dp },
            )
        }

        val winner = presentation.winnerLabel
        val margin = presentation.margin
        if (winner != null && margin != null) {
            SectionLabel(Icons.Filled.EmojiEvents, "$winner, +${CatalanNumbers.grouped(margin)} punts", emphasized = true)
        } else {
            SectionLabel(Icons.Filled.DragHandle, "Empat", emphasized = true)
        }
    }
}

@Composable
private fun ComparisonCastellCell(castell: ComparisonPresentation.Castell?) {
    if (castell == null) {
        Text("—", style = cellStyle, color = CastellsTheme.colors.tertiaryText)
        return
    }
    Column(horizontalAlignment = Alignment.End, modifier = Modifier.alpha(if (castell.counted) 1f else 0.55f)) {
        Text(castell.notation, style = notationStyle)
        val suffix = if (castell.counted) "" else " · no compta"
        Text(
            text = "${castell.result} · ${CatalanNumbers.grouped(castell.points)}$suffix",
            style = detailStyle.merge(TabularNumbers),
            color = CastellsTheme.colors.secondaryText,
        )
    }
}

@Composable
internal fun ScoreRanking(presentation: ScorePresentation) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        SectionLabel(Icons.Filled.FormatListNumbered, presentation.title)
        TableSurface {
            val secondary = CastellsTheme.colors.secondaryText
            val pointHeaders = when (presentation.outcome) {
                ScorePresentation.Outcome.LOADED -> listOf("Carregat")
                ScorePresentation.Outcome.UNLOADED -> listOf("Descarregat")
                ScorePresentation.Outcome.BOTH -> listOf("Carregat", "Descarregat")
            }
            val header = TableRow.Cells(
                (listOf("#", "Castell") + pointHeaders).map { title ->
                    { Text(title, style = cellStyle, color = secondary) }
                },
            )
            val rows = presentation.rows.map { row ->
                val points = when (presentation.outcome) {
                    ScorePresentation.Outcome.LOADED -> listOf(row.loadedPoints)
                    ScorePresentation.Outcome.UNLOADED -> listOf(row.unloadedPoints)
                    ScorePresentation.Outcome.BOTH -> listOf(row.loadedPoints, row.unloadedPoints)
                }
                TableRow.Cells(
                    listOf<@Composable () -> Unit>(
                        { Text("${row.position}", style = cellStyle.merge(TabularNumbers), color = secondary) },
                        {
                            Text(
                                text = row.notation,
                                style = notationStyle,
                                color = if (row.notation == presentation.focusNotation) {
                                    MaterialTheme.colorScheme.primary
                                } else {
                                    LocalContentColor.current
                                },
                            )
                        },
                    ) + points.map { value ->
                        { Text(CatalanNumbers.grouped(value), style = cellStyle.merge(TabularNumbers)) }
                    },
                )
            }
            ScoreTable(
                rows = listOf(header, TableRow.Divider) + rows,
                columnCount = 2 + pointHeaders.size,
                minColumnWidths = listOf(22.dp, 76.dp) + pointHeaders.map { if (it == "Carregat") 66.dp else 86.dp },
                columnSpacing = 13.dp,
                // Positions line up on the right; the castell names on the left.
                columnAlignment = { if (it == 1) Alignment.CenterStart else Alignment.CenterEnd },
            )
        }
    }
}

@Composable
internal fun PerformanceSummary(presentation: PerformanceSummaryPresentation) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        SectionLabel(Icons.Filled.Functions, presentation.title)
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(11.dp))
                .background(tableBackground)
                .padding(11.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            for (row in presentation.rows) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .alpha(if (row.counted) 1f else 0.55f),
                        verticalArrangement = Arrangement.spacedBy(2.dp),
                    ) {
                        Text(row.notation, style = notationStyle)
                        Text(row.result, style = detailStyle, color = CastellsTheme.colors.secondaryText)
                    }
                    Text(
                        text = CatalanNumbers.grouped(row.points),
                        style = cellStyle.merge(TabularNumbers),
                        color = if (row.counted) LocalContentColor.current else CastellsTheme.colors.secondaryText,
                    )
                }
            }
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Row {
                Text("Total", fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
                Text(
                    text = CatalanNumbers.grouped(presentation.total),
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge.merge(TabularNumbers),
                )
            }
        }
    }
}

@Composable
private fun TableSurface(content: @Composable () -> Unit) {
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(11.dp))
            .background(tableBackground)
            .horizontalScroll(rememberScrollState())
            .padding(10.dp),
    ) {
        content()
    }
}

@Composable
private fun SectionLabel(icon: ImageVector, text: String, emphasized: Boolean = false) {
    val color = if (emphasized) LocalContentColor.current else CastellsTheme.colors.secondaryText
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(18.dp))
        Text(text = text, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold, color = color)
    }
}
