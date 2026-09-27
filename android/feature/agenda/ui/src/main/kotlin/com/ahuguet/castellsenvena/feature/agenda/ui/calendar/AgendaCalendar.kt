package com.ahuguet.castellsenvena.feature.agenda.ui.calendar

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PagerState
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.layout.layout
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarFold
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarPaging
import com.ahuguet.castellsenvena.feature.agenda.ui.AgendaFoldState
import java.time.LocalDate
import kotlin.math.abs
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/** A vertical swipe this long over the calendar folds or unfolds it. */
private val ToggleDragDistance = 36.dp

/**
 * The calendar above the event list: a month that folds into its active week.
 * Months and weeks change by swiping sideways.
 */
@Composable
internal fun AgendaCalendar(
    selectedDate: LocalDate,
    visibleMonth: LocalDate,
    visibleWeek: LocalDate,
    eventDateKeys: Set<String>,
    isGroupFilterActive: Boolean,
    selectedGroupCount: Int,
    foldState: AgendaFoldState,
    onToggle: () -> Unit,
    onOpenFilter: () -> Unit,
    onSelect: (LocalDate) -> Unit,
    onShowMonth: (LocalDate) -> Unit,
    onShowWeek: (LocalDate) -> Unit,
    modifier: Modifier = Modifier,
) {
    val isCollapsed = foldState.isCollapsed
    val days = CalendarDays(selectedDate = selectedDate, today = AgendaCalendarMath.today(), eventDateKeys = eventDateKeys)
    val toggleDistance = with(LocalDensity.current) { ToggleDragDistance.toPx() }
    var verticalDrag by remember { mutableFloatStateOf(0f) }

    Column(
        modifier = modifier.draggable(
            state = rememberDraggableState { delta -> verticalDrag += delta },
            orientation = Orientation.Vertical,
            onDragStarted = { verticalDrag = 0f },
            onDragStopped = {
                // Up folds an unfolded calendar; down unfolds a folded one.
                if (abs(verticalDrag) >= toggleDistance && (verticalDrag < 0f) != foldState.isCollapsed) onToggle()
            },
        ),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        AgendaCalendarHeader(
            title = AgendaCalendarMath.monthTitle(if (isCollapsed) visibleWeek else visibleMonth),
            isCollapsed = isCollapsed,
            isGroupFilterActive = isGroupFilterActive,
            selectedGroupCount = selectedGroupCount,
            onToggle = onToggle,
            onOpenFilter = onOpenFilter,
        )

        if (foldState.isFullyFolded) {
            AgendaWeekPager(visibleWeek = visibleWeek, days = days, onSelect = onSelect, onShowWeek = onShowWeek)
        } else {
            AgendaMonthPager(
                visibleMonth = visibleMonth,
                visibleWeek = visibleWeek,
                days = days,
                foldState = foldState,
                onSelect = onSelect,
                onShowMonth = onShowMonth,
            )
        }
    }
}

@Composable
private fun AgendaCalendarHeader(
    title: String,
    isCollapsed: Boolean,
    isGroupFilterActive: Boolean,
    selectedGroupCount: Int,
    onToggle: () -> Unit,
    onOpenFilter: () -> Unit,
) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Row(
            modifier = Modifier
                .clip(RoundedCornerShape(8.dp))
                .clickable(
                    onClickLabel = if (isCollapsed) "Mostra el calendari mensual" else "Plega el calendari mensual",
                    onClick = onToggle,
                )
                .semantics {
                    heading()
                    stateDescription = if (isCollapsed) "Plegat" else "Desplegat"
                }
                .padding(vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
            Icon(
                imageVector = if (isCollapsed) Icons.Filled.KeyboardArrowDown else Icons.Filled.KeyboardArrowUp,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.weight(1f))
        GroupFilterButton(isActive = isGroupFilterActive, selectedGroupCount = selectedGroupCount, onClick = onOpenFilter)
    }
}

/** Shows how many groups the agenda follows while it only shows some. */
@Composable
private fun GroupFilterButton(isActive: Boolean, selectedGroupCount: Int, onClick: () -> Unit) {
    IconButton(
        onClick = onClick,
        modifier = Modifier.semantics {
            contentDescription = "Filtra l'agenda per colles"
            stateDescription = when {
                !isActive -> "Totes les colles"
                selectedGroupCount == 1 -> "1 colla seleccionada"
                else -> "$selectedGroupCount colles seleccionades"
            }
        },
    ) {
        BadgedBox(
            badge = {
                if (isActive) {
                    // The state description already says it.
                    Badge(modifier = Modifier.clearAndSetSemantics {}) { Text("$selectedGroupCount") }
                }
            },
        ) {
            Icon(
                imageVector = Icons.Filled.FilterList,
                contentDescription = null,
                tint = if (isActive) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun AgendaMonthPager(
    visibleMonth: LocalDate,
    visibleWeek: LocalDate,
    days: CalendarDays,
    foldState: AgendaFoldState,
    onSelect: (LocalDate) -> Unit,
    onShowMonth: (LocalDate) -> Unit,
) {
    val visiblePage = AgendaCalendarPaging.monthPage(visibleMonth)
    val pagerState = rememberPagerState(initialPage = visiblePage) { AgendaCalendarPaging.MONTH_PAGE_COUNT }
    PagerFollowsModel(pagerState, visiblePage) { page -> onShowMonth(AgendaCalendarPaging.month(page)) }
    val scope = rememberCoroutineScope()
    val reduceMotion = LocalReduceMotion.current
    val progress = { foldState.displayedProgress }

    HorizontalPager(
        state = pagerState,
        modifier = Modifier
            .fillMaxWidth()
            .clipToBounds()
            .monthPagerHeight(pagerState, progress)
            .pagingActions(pagerState, scope, reduceMotion, previous = "Mes anterior", next = "Mes següent"),
        verticalAlignment = Alignment.Top,
    ) { page ->
        AgendaMonthGrid(
            month = AgendaCalendarPaging.month(page),
            visibleWeek = visibleWeek,
            days = days,
            progress = progress,
            isCollapsed = foldState.isCollapsed,
            onSelect = onSelect,
            modifier = Modifier.wrapContentHeight(align = Alignment.Top, unbounded = true),
        )
    }
}

@Composable
private fun AgendaWeekPager(
    visibleWeek: LocalDate,
    days: CalendarDays,
    onSelect: (LocalDate) -> Unit,
    onShowWeek: (LocalDate) -> Unit,
) {
    val visiblePage = AgendaCalendarPaging.weekPage(visibleWeek)
    val pagerState = rememberPagerState(initialPage = visiblePage) { AgendaCalendarPaging.WEEK_PAGE_COUNT }
    PagerFollowsModel(pagerState, visiblePage) { page -> onShowWeek(AgendaCalendarPaging.week(page)) }
    val scope = rememberCoroutineScope()
    val reduceMotion = LocalReduceMotion.current

    HorizontalPager(
        state = pagerState,
        modifier = Modifier
            .fillMaxWidth()
            .height(AgendaCalendarFold.COLLAPSED_GRID_HEIGHT.dp)
            .pagingActions(pagerState, scope, reduceMotion, previous = "Setmana anterior", next = "Setmana següent"),
        verticalAlignment = Alignment.Top,
    ) { page ->
        AgendaWeekGrid(weekStart = AgendaCalendarPaging.week(page), days = days, onSelect = onSelect)
    }
}

/**
 * Keeps a pager and the model on the same page: a settled swipe moves the
 * model, and a day selected in another month or week moves the pager.
 */
@Composable
private fun PagerFollowsModel(pagerState: PagerState, visiblePage: Int, onPageSettled: (Int) -> Unit) {
    val currentOnPageSettled by rememberUpdatedState(onPageSettled)
    LaunchedEffect(pagerState) {
        snapshotFlow { pagerState.settledPage }.collect { page -> currentOnPageSettled(page) }
    }
    LaunchedEffect(pagerState, visiblePage) {
        if (!pagerState.isScrollInProgress && pagerState.currentPage != visiblePage) {
            pagerState.scrollToPage(visiblePage)
        }
    }
}

/** Previous and next page as accessibility actions. */
private fun Modifier.pagingActions(
    pagerState: PagerState,
    scope: CoroutineScope,
    reduceMotion: Boolean,
    previous: String,
    next: String,
): Modifier = semantics {
    fun goTo(page: Int): Boolean {
        if (page !in 0 until pagerState.pageCount) return false
        scope.launch {
            if (reduceMotion) pagerState.scrollToPage(page) else pagerState.animateScrollToPage(page)
        }
        return true
    }
    customActions = listOf(
        CustomAccessibilityAction(previous) { goTo(pagerState.currentPage - 1) },
        CustomAccessibilityAction(next) { goTo(pagerState.currentPage + 1) },
    )
}

/**
 * The month pager is as tall as its month at the current fold, and blends
 * into the height of the next month while swiping to a month with more or
 * fewer weeks. Read during layout, so neither drives recomposition.
 */
private fun Modifier.monthPagerHeight(pagerState: PagerState, progress: () -> Float): Modifier =
    layout { measurable, constraints ->
        val fold = progress()
        val page = pagerState.currentPage
        val offset = pagerState.currentPageOffsetFraction
        val current = monthGridHeight(page, fold)
        val heightDp = if (offset == 0f) {
            current
        } else {
            val neighbour = monthGridHeight(page + if (offset > 0f) 1 else -1, fold)
            current + (neighbour - current) * abs(offset)
        }
        val height = heightDp.dp.roundToPx()
        val placeable = measurable.measure(constraints.copy(minHeight = height, maxHeight = height))
        layout(placeable.width, height) { placeable.place(0, 0) }
    }

private fun monthGridHeight(page: Int, progress: Float): Float = AgendaCalendarFold.gridHeight(
    weekRowCount = AgendaCalendarMath.monthWeekRowCount(AgendaCalendarPaging.month(page)),
    progress = progress,
)
