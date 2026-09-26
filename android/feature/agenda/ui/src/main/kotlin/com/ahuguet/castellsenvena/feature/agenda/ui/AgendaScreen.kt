package com.ahuguet.castellsenvena.feature.agenda.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaViewModel
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarFold
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarMath
import com.ahuguet.castellsenvena.feature.agenda.ui.calendar.AgendaCalendar
import com.ahuguet.castellsenvena.feature.agenda.ui.events.AgendaEventList
import com.ahuguet.castellsenvena.feature.agenda.ui.groupfilter.AgendaGroupFilterSheet
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

/**
 * The Agenda: a calendar that folds into a week as the day's events scroll.
 * [showsGroupFilter] is hoisted so Ajustos can open the group filter too.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AgendaScreen(
    model: AgendaViewModel,
    showsGroupFilter: Boolean,
    onShowsGroupFilterChange: (Boolean) -> Unit,
    onOpenLink: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by model.state.collectAsState()
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()
    val foldDistance = with(LocalDensity.current) {
        AgendaCalendarFold.foldDistance(AgendaCalendarMath.monthWeekRowCount(state.visibleMonth)).dp.toPx()
    }
    val foldState = rememberAgendaFoldState(listState, foldDistance, LocalReduceMotion.current)
    var isRefreshing by remember { mutableStateOf(false) }

    LaunchedEffect(model) {
        launch { model.load() }
        launch { model.loadGroupDirectory() }
    }
    LaunchedEffect(model, foldState) {
        // A new group selection shows the whole month again.
        model.state.map { it.groupFilter.selection }.distinctUntilChanged().drop(1).collect { foldState.reset() }
    }
    LaunchedEffect(model, listState) {
        // Another day starts from its first event.
        model.state.map { it.selectedDate }.distinctUntilChanged().drop(1).collect { listState.scrollToItem(0) }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top + WindowInsetsSides.Horizontal)),
    ) {
        AgendaCalendar(
            selectedDate = state.selectedDate,
            visibleMonth = state.visibleMonth,
            visibleWeek = state.visibleWeek,
            eventDateKeys = state.eventDateKeys,
            isGroupFilterActive = state.groupFilter.isActive,
            selectedGroupCount = state.groupFilter.selectedGroupCount,
            foldState = foldState,
            onToggle = { scope.launch { foldState.toggle() } },
            onOpenFilter = { onShowsGroupFilterChange(true) },
            onSelect = { date -> scope.launch { model.selectAndLoad(date) } },
            onShowMonth = { month -> scope.launch { model.showMonth(containing = month) } },
            onShowWeek = { week -> scope.launch { model.showWeek(containing = week) } },
            modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 12.dp),
        )
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = {
                scope.launch {
                    isRefreshing = true
                    try {
                        model.refresh()
                    } finally {
                        isRefreshing = false
                    }
                }
            },
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
        ) {
            AgendaEventList(
                events = state.events,
                otherEvents = state.otherEvents,
                isLoading = state.isLoading,
                errorMessage = state.errorMessage,
                sourceStatus = state.sourceStatus,
                officialUrl = model.officialUrl,
                listState = listState,
                onRetry = { scope.launch { model.refresh() } },
                onOpenLink = onOpenLink,
                modifier = Modifier
                    .fillMaxSize()
                    .nestedScroll(foldState.nestedScrollConnection),
            )
        }
    }

    if (showsGroupFilter) {
        AgendaGroupFilterSheet(
            model = model,
            filter = state.groupFilter,
            directoryErrorMessage = state.groupDirectoryErrorMessage,
            onDismiss = { onShowsGroupFilterChange(false) },
        )
    }
}
