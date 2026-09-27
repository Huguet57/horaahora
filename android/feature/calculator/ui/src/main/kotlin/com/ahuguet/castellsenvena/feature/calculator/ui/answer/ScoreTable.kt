package com.ahuguet.castellsenvena.feature.calculator.ui.answer

import androidx.compose.foundation.layout.Box
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.layout.Placeable
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp

/** A row of a [ScoreTable]: one cell per column, or a divider across the table. */
internal sealed interface TableRow {
    class Cells(val cells: List<@Composable () -> Unit>) : TableRow

    data object Divider : TableRow
}

/**
 * A small grid whose columns are as wide as their widest cell, like the
 * tables of the iOS app. Cells are centred vertically within their row and
 * aligned within their column by [columnAlignment]. It sits in a horizontal
 * scroll, so cells never wrap.
 */
@Composable
internal fun ScoreTable(
    rows: List<TableRow>,
    columnCount: Int,
    modifier: Modifier = Modifier,
    minColumnWidths: List<Dp> = emptyList(),
    columnSpacing: Dp = 14.dp,
    rowSpacing: Dp = 8.dp,
    columnAlignment: (column: Int) -> Alignment = { if (it == 0) Alignment.CenterStart else Alignment.CenterEnd },
) {
    val dividerColor = MaterialTheme.colorScheme.outlineVariant
    Layout(
        modifier = modifier,
        content = {
            for (row in rows) {
                when (row) {
                    is TableRow.Cells -> for (cell in row.cells) Box { cell() }
                    TableRow.Divider -> HorizontalDivider(color = dividerColor)
                }
            }
        },
    ) { measurables, _ ->
        val widths = IntArray(columnCount) { column -> minColumnWidths.getOrNull(column)?.roundToPx() ?: 0 }
        var next = 0
        // Cells first, to size the columns; dividers once the width is known.
        val measuredRows: List<List<Placeable>?> = rows.map { row ->
            when (row) {
                is TableRow.Cells -> row.cells.indices.map { column ->
                    measurables[next++].measure(Constraints()).also { widths[column] = maxOf(widths[column], it.width) }
                }
                TableRow.Divider -> {
                    next++
                    null
                }
            }
        }
        val spacing = columnSpacing.roundToPx()
        val tableWidth = widths.sum() + spacing * (columnCount - 1).coerceAtLeast(0)
        next = 0
        val dividers = rows.mapNotNull { row ->
            when (row) {
                is TableRow.Cells -> {
                    next += row.cells.size
                    null
                }
                TableRow.Divider -> measurables[next++].measure(Constraints.fixedWidth(tableWidth))
            }
        }
        val rowGap = rowSpacing.roundToPx()
        var measuredDividers = 0
        val heights = measuredRows.map { cells ->
            if (cells != null) cells.maxOfOrNull { it.height } ?: 0 else dividers[measuredDividers++].height
        }
        val tableHeight = heights.sum() + rowGap * (rows.size - 1).coerceAtLeast(0)

        layout(tableWidth, tableHeight) {
            var y = 0
            var dividerIndex = 0
            measuredRows.forEachIndexed { index, cells ->
                if (cells == null) {
                    dividers[dividerIndex++].place(0, y)
                } else {
                    var x = 0
                    cells.forEachIndexed { column, cell ->
                        val offset = columnAlignment(column).align(
                            size = IntSize(cell.width, cell.height),
                            space = IntSize(widths[column], heights[index]),
                            layoutDirection = LayoutDirection.Ltr,
                        )
                        cell.placeRelative(x + offset.x, y + offset.y)
                        x += widths[column] + spacing
                    }
                }
                y += heights[index] + rowGap
            }
        }
    }
}
