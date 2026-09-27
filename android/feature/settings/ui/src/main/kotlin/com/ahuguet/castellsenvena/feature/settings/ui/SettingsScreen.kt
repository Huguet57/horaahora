package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

private enum class SettingsDestination {
    ROOT,
    NOTIFICATION_INTEREST,
    SOURCES,
}

/**
 * Ajustos and its two subpages. Notification changes run in [actionScope],
 * so a permission request answered after leaving the screen still applies.
 */
@Composable
fun SettingsScreen(
    model: SettingsModel,
    configuration: SettingsConfiguration,
    hasFollowedGroups: Boolean,
    actionScope: CoroutineScope,
    onChooseGroups: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by model.state.collectAsState()
    var destination by rememberSaveable { mutableStateOf(SettingsDestination.ROOT) }
    val reduceMotion = LocalReduceMotion.current

    LaunchedEffect(model) { model.refreshNotificationStatus() }
    BackHandler(enabled = destination != SettingsDestination.ROOT) { destination = SettingsDestination.ROOT }

    AnimatedContent(
        targetState = destination,
        modifier = modifier,
        transitionSpec = {
            when {
                reduceMotion -> EnterTransition.None togetherWith ExitTransition.None
                targetState != SettingsDestination.ROOT ->
                    (slideInHorizontally { it } togetherWith slideOutHorizontally { -it / 4 } + fadeOut())
                        .apply { targetContentZIndex = 1f }
                else -> (slideInHorizontally { -it / 4 } togetherWith slideOutHorizontally { it })
                    .apply { targetContentZIndex = -1f }
            }
        },
        label = "settings",
    ) { target ->
        when (target) {
            SettingsDestination.ROOT -> SettingsRoot(
                state = state,
                configuration = configuration,
                onNotificationsEnabledChange = { enabled ->
                    actionScope.launch { model.setHourByHourNotificationsEnabled(enabled) }
                },
                onOpenNotificationInterest = { destination = SettingsDestination.NOTIFICATION_INTEREST },
                onOpenSystemSettings = { actionScope.launch { model.openSystemSettings() } },
                onOpenSources = { destination = SettingsDestination.SOURCES },
                onOpenUrl = onOpenUrl,
                onContactSupport = onContactSupport,
                onCopyIdentifier = onCopyIdentifier,
                onSecretTap = {
                    if (model.registerSecretTap()) model.state.value.showsHiddenSections else null
                },
            )

            SettingsDestination.NOTIFICATION_INTEREST -> NotificationInterestScreen(
                state = state,
                hasFollowedGroups = hasFollowedGroups,
                onSelect = { level -> actionScope.launch { model.setMinimumInterest(level) } },
                onChooseGroups = onChooseGroups,
                onBack = { destination = SettingsDestination.ROOT },
            )

            SettingsDestination.SOURCES -> SourcesAndCreditsScreen(
                configuration = configuration,
                showsHiddenSections = state.showsHiddenSections,
                onOpenUrl = onOpenUrl,
                onBack = { destination = SettingsDestination.ROOT },
            )
        }
    }
}
