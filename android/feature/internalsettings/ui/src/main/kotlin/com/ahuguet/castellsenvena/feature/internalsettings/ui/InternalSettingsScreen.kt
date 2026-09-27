package com.ahuguet.castellsenvena.feature.internalsettings.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSettingsModel
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSources
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.ui.SettingsScreen
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

private const val NOTIFICATION_INTEREST = "castells.settings.notification-interest"

/**
 * Ajustos in the internal app: the calculator's settings, plus the news notifications and
 * the sources of Hora a Hora and Agenda while those sections show, and the secret gesture
 * on the version row. Notification changes run in [actionScope], so a permission request
 * answered after leaving the screen still applies.
 */
@Composable
fun InternalSettingsScreen(
    model: InternalSettingsModel,
    configuration: SettingsConfiguration,
    sources: InternalSources,
    hasFollowedGroups: Boolean,
    actionScope: CoroutineScope,
    onChooseGroups: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by model.state.collectAsState()

    LaunchedEffect(model) { model.refreshNotificationStatus() }

    SettingsScreen(
        configuration = configuration,
        onOpenUrl = onOpenUrl,
        onContactSupport = onContactSupport,
        onCopyIdentifier = onCopyIdentifier,
        modifier = modifier,
        additionalCredits = if (state.showsHiddenSections) sources.credits else emptyList(),
        onVersionTap = model::versionTapMessage,
        subpage = { key, onBack ->
            if (key == NOTIFICATION_INTEREST) {
                NotificationInterestScreen(
                    state = state,
                    hasFollowedGroups = hasFollowedGroups,
                    onSelect = { level -> actionScope.launch { model.setMinimumInterest(level) } },
                    onChooseGroups = onChooseGroups,
                    onBack = onBack,
                )
            }
        },
        leadingContent = { openSubpage ->
            if (state.showsHiddenSections) {
                NotificationSection(
                    state = state,
                    onEnabledChange = { enabled ->
                        actionScope.launch { model.setHourByHourNotificationsEnabled(enabled) }
                    },
                    onOpenInterest = { openSubpage(NOTIFICATION_INTEREST) },
                    onOpenSystemSettings = { actionScope.launch { model.openSystemSettings() } },
                )
            }
        },
    )
}
