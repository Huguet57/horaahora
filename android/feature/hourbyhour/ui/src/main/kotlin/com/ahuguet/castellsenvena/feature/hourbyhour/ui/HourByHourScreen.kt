package com.ahuguet.castellsenvena.feature.hourbyhour.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.common.CatalanDates
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourState
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourViewModel
import java.time.ZoneId
import kotlinx.coroutines.launch

/**
 * The Hora a Hora feed, grouped by day. Items with their own link open it;
 * the others show their full text in a sheet.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HourByHourScreen(
    model: HourByHourViewModel,
    showsNotificationOnboarding: Boolean,
    onConfigureNotifications: () -> Unit,
    onDismissNotificationOnboarding: () -> Unit,
    onOpenLink: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by model.state.collectAsState()
    val scope = rememberCoroutineScope()
    var isRefreshing by remember { mutableStateOf(false) }
    var detailItemId by rememberSaveable { mutableStateOf<String?>(null) }
    val scrollBehavior = TopAppBarDefaults.exitUntilCollapsedScrollBehavior()
    val zone = remember { ZoneId.systemDefault() }

    val refresh: () -> Unit = {
        if (!isRefreshing) {
            scope.launch {
                isRefreshing = true
                try {
                    model.refresh()
                } finally {
                    isRefreshing = false
                }
            }
        }
    }

    LaunchedEffect(model) { model.loadIfNeeded() }

    Scaffold(
        modifier = modifier,
        topBar = {
            LargeTopAppBar(
                title = { Text("Hora a Hora") },
                scrollBehavior = scrollBehavior,
            )
        },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
        ) {
            when {
                state.items.isEmpty() && state.isLoading -> HourByHourSkeleton()

                state.items.isEmpty() && state.errorMessage != null -> ContentUnavailable(
                    icon = Icons.Filled.WifiOff,
                    title = "No s'ha pogut carregar",
                    description = state.errorMessage,
                    action = { Button(onClick = refresh) { Text("Torna-ho a provar") } },
                )

                state.items.isEmpty() -> ContentUnavailable(
                    icon = Icons.Filled.Schedule,
                    title = "Encara no hi ha entrades",
                )

                else -> PullToRefreshBox(isRefreshing = isRefreshing, onRefresh = refresh) {
                    HourByHourList(
                        state = state,
                        zone = zone,
                        showsNotificationOnboarding = showsNotificationOnboarding,
                        onConfigureNotifications = onConfigureNotifications,
                        onDismissNotificationOnboarding = onDismissNotificationOnboarding,
                        onOpen = { item ->
                            val link = item.associatedUrl
                            if (link != null) onOpenLink(link) else detailItemId = item.id
                        },
                        onLastItemShown = { item -> model.loadNextIfNeeded(after = item) },
                        // Inside the pull to refresh, so scrolling back up expands the
                        // large title before it starts a refresh.
                        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
                    )
                }
            }
        }
    }

    val detailItem = detailItemId?.let { id -> state.items.firstOrNull { it.id == id } }
    if (detailItem != null) {
        HourByHourDetailSheet(item = detailItem, zone = zone, onDismiss = { detailItemId = null })
    }
}

@Composable
private fun HourByHourList(
    state: HourByHourState,
    zone: ZoneId,
    showsNotificationOnboarding: Boolean,
    onConfigureNotifications: () -> Unit,
    onDismissNotificationOnboarding: () -> Unit,
    onOpen: (HourByHourItem) -> Unit,
    onLastItemShown: suspend (HourByHourItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val reduceMotion = LocalReduceMotion.current
    val lastItemId = state.items.lastOrNull()?.id

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 24.dp),
    ) {
        if (showsNotificationOnboarding) {
            item(key = "notification-onboarding") {
                NotificationOnboardingCard(
                    onConfigure = onConfigureNotifications,
                    onDismiss = onDismissNotificationOnboarding,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                )
            }
        }

        for (group in state.dayGroups) {
            item(key = group.id, contentType = "day") {
                SectionHeader(
                    text = group.day?.let(CatalanDates::fullDate) ?: "Sense data",
                    modifier = if (reduceMotion) Modifier else Modifier.animateItem(),
                )
            }
            itemsIndexed(group.items, key = { _, item -> item.id }, contentType = { _, _ -> "item" }) { index, item ->
                HourByHourRow(
                    item = item,
                    zone = zone,
                    showsDivider = index < group.items.lastIndex,
                    onClick = { onOpen(item) },
                    modifier = if (reduceMotion) Modifier else Modifier.animateItem(),
                )
                if (item.id == lastItemId) {
                    LaunchedEffect(item.id) { onLastItemShown(item) }
                }
            }
        }

        if (state.isLoadingMore) {
            item(key = "loading-more") {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }
            }
        }
    }
}
