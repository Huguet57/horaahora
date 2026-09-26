package com.ahuguet.castellsenvena.feature.agenda.ui.calendar

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.ripple
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.layout
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarFold
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import java.time.LocalDate
import java.time.YearMonth

private val Weekdays = listOf("DL", "DT", "DC", "DJ", "DV", "DS", "DG")
private val DaySpacing = 4.dp

/** What every day cell needs to know besides its own date. */
@Immutable
internal data class CalendarDays(
    val selectedDate: LocalDate,
    val today: LocalDate,
    val eventDateKeys: Set<String>,
)

/**
 * One month in Monday-based weeks. The active week keeps its full slot while
 * the other weeks shrink and fade as [progress] folds the calendar.
 */
@Composable
internal fun AgendaMonthGrid(
    month: LocalDate,
    visibleWeek: LocalDate,
    days: CalendarDays,
    progress: () -> Float,
    isCollapsed: Boolean,
    onSelect: (LocalDate) -> Unit,
    modifier: Modifier = Modifier,
) {
    val yearMonth = YearMonth.from(month)
    val rows = AgendaCalendarMath.monthWeekRows(month)
    val activeRow = AgendaCalendarMath.weekRowIndex(visibleWeek, rows) ?: 0

    Column(modifier = modifier.fillMaxWidth()) {
        WeekdayHeader()
        rows.forEachIndexed { index, dates ->
            val isActive = index == activeRow
            WeekRowSlot(isActive = isActive, progress = progress, isHidden = !isActive && isCollapsed) {
                for (date in dates) {
                    when {
                        YearMonth.from(date) == yearMonth -> DayCell(date, days, onSelect, Modifier.weight(1f))

                        // Days of the neighbouring months complete the folded week.
                        isActive -> DayCell(
                            date = date,
                            days = days,
                            onSelect = onSelect,
                            enabled = isCollapsed,
                            modifier = Modifier
                                .weight(1f)
                                .graphicsLayer { alpha = progress() }
                                .then(if (isCollapsed) Modifier else Modifier.clearAndSetSemantics {}),
                        )

                        else -> Spacer(Modifier.weight(1f))
                    }
                }
            }
        }
    }
}

/** The single week shown while the calendar is folded. */
@Composable
internal fun AgendaWeekGrid(weekStart: LocalDate, days: CalendarDays, onSelect: (LocalDate) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth()) {
        WeekdayHeader()
        WeekRowSlot(isActive = true, progress = { 1f }, isHidden = false) {
            for (date in AgendaCalendarMath.week(weekStart)) {
                DayCell(date, days, onSelect, Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun WeekdayHeader() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(AgendaCalendarFold.WEEKDAY_HEADER_HEIGHT.dp)
            // Every day already reads its full date.
            .clearAndSetSemantics {},
        horizontalArrangement = Arrangement.spacedBy(DaySpacing),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        for (weekday in Weekdays) {
            Text(
                text = weekday,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
                color = CastellsTheme.colors.tertiaryText,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/**
 * A week row at the bottom of its slot: the gap above the row plus the row.
 * Inactive rows lose height and opacity with the fold; both are read during
 * layout and drawing, so folding does not recompose the grid.
 */
@Composable
private fun WeekRowSlot(
    isActive: Boolean,
    progress: () -> Float,
    isHidden: Boolean,
    content: @Composable RowScope.() -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .graphicsLayer {
                clip = true
                alpha = if (isActive) 1f else 1f - progress()
            }
            .layout { measurable, constraints ->
                val slotHeight = if (isActive) {
                    AgendaCalendarFold.WEEK_ROW_SLOT_HEIGHT
                } else {
                    AgendaCalendarFold.inactiveWeekRowSlotHeight(progress())
                }
                val slot = slotHeight.dp.roundToPx()
                val row = AgendaCalendarFold.WEEK_ROW_HEIGHT.dp.roundToPx()
                val placeable = measurable.measure(constraints.copy(minHeight = row, maxHeight = row))
                layout(placeable.width, slot) { placeable.place(0, slot - row) }
            }
            .then(if (isHidden) Modifier.clearAndSetSemantics {} else Modifier),
        horizontalArrangement = Arrangement.spacedBy(DaySpacing),
        verticalAlignment = Alignment.CenterVertically,
        content = content,
    )
}

@Composable
private fun DayCell(
    date: LocalDate,
    days: CalendarDays,
    onSelect: (LocalDate) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    val isSelected = date == days.selectedDate
    val isToday = date == days.today
    val isPast = date.isBefore(days.today)
    val hasEvents = AgendaCalendarMath.localDateKey(date) in days.eventDateKeys
    val colors = MaterialTheme.colorScheme

    Box(
        modifier = modifier
            .height(AgendaCalendarFold.WEEK_ROW_HEIGHT.dp)
            .alpha(if (isPast && !isSelected) 0.35f else 1f)
            .selectable(
                selected = isSelected,
                interactionSource = null,
                indication = ripple(bounded = false, radius = 22.dp),
                enabled = enabled,
                role = Role.Button,
                onClick = { onSelect(date) },
            )
            .semantics {
                contentDescription = AgendaCalendarMath.accessibilityDate(date)
                if (hasEvents) stateDescription = "Té actuacions"
            },
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .size(42.dp)
                .background(if (isSelected) colors.primary else Color.Transparent, CircleShape),
        )
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text(
                text = date.dayOfMonth.toString(),
                style = MaterialTheme.typography.bodyLarge.merge(TabularNumbers),
                color = when {
                    isSelected -> colors.onPrimary
                    isToday -> colors.primary
                    else -> colors.onSurface
                },
                modifier = Modifier.clearAndSetSemantics {},
            )
            Box(
                modifier = Modifier
                    .size(5.dp)
                    .background(
                        color = when {
                            !hasEvents -> Color.Transparent
                            isSelected -> colors.onPrimary
                            else -> colors.primary
                        },
                        shape = CircleShape,
                    ),
            )
        }
    }
}
