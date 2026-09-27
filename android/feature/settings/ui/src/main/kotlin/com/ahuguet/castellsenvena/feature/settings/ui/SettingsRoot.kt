package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.outlined.ContentCopy
import androidx.compose.material.icons.outlined.Email
import androidx.compose.material.icons.outlined.FrontHand
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ExternalLinkIcon
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.feature.settings.presentation.HourByHourNotificationStatus
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsState
import com.ahuguet.castellsenvena.feature.settings.presentation.settingsTitle
import kotlinx.coroutines.delay

@Composable
internal fun SettingsRoot(
    state: SettingsState,
    configuration: SettingsConfiguration,
    onNotificationsEnabledChange: (Boolean) -> Unit,
    onOpenNotificationInterest: () -> Unit,
    onOpenSystemSettings: () -> Unit,
    onOpenSources: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
    onSecretTap: () -> Boolean?,
) {
    SettingsScaffold(title = "Ajustos") {
        if (state.showsHiddenSections) {
            NotificationSection(
                state = state,
                onEnabledChange = onNotificationsEnabledChange,
                onOpenInterest = onOpenNotificationInterest,
                onOpenSystemSettings = onOpenSystemSettings,
            )
        }

        SectionHeader("Privacitat i dades")
        ListRow(
            title = "Política de privacitat",
            leadingIcon = Icons.Outlined.FrontHand,
            onClick = { onOpenUrl(configuration.privacyUrl) },
            trailing = { ExternalLinkIcon() },
        )

        SectionHeader("Ajuda")
        ListRow(
            title = "Contacta amb suport",
            leadingIcon = Icons.Outlined.Email,
            onClick = { onContactSupport(configuration.supportEmailUrl) },
            trailing = { ExternalLinkIcon() },
        )
        CopyIdentifierRow(identifier = configuration.technicalIdentifier, onCopy = onCopyIdentifier)

        SectionHeader("Sobre ${configuration.appName}")
        VersionRow(configuration = configuration, onSecretTap = onSecretTap)
        ListRow(
            title = "Fonts i crèdits",
            leadingIcon = Icons.AutoMirrored.Outlined.MenuBook,
            onClick = onOpenSources,
        )
    }
}

@Composable
private fun NotificationSection(
    state: SettingsState,
    onEnabledChange: (Boolean) -> Unit,
    onOpenInterest: () -> Unit,
    onOpenSystemSettings: () -> Unit,
) {
    val status = state.notificationStatus
    val isEnabled = status == HourByHourNotificationStatus.ENABLED

    SectionHeader("Notificacions")
    ListRow(
        title = "Avisos de notícies",
        leadingIcon = Icons.Outlined.Notifications,
        enabled = state.canToggleNotifications,
        modifier = Modifier.toggleable(
            value = isEnabled,
            enabled = state.canToggleNotifications,
            role = Role.Switch,
            onValueChange = onEnabledChange,
        ),
        trailing = {
            Switch(checked = isEnabled, onCheckedChange = null, enabled = state.canToggleNotifications)
        },
    )
    ListRow(
        title = "Quines notícies?",
        subtitle = state.minimumInterest.settingsTitle,
        leadingIcon = Icons.Outlined.Tune,
        enabled = status != HourByHourNotificationStatus.LOADING,
        onClick = onOpenInterest,
    )
    if (status == HourByHourNotificationStatus.DENIED) {
        MessageRow(text = "Bloquejades per Android", color = CastellsTheme.colors.warning)
        ListRow(
            title = "Obre els ajustos del sistema",
            leadingIcon = Icons.Outlined.Settings,
            leadingIconTint = MaterialTheme.colorScheme.primary,
            titleColor = MaterialTheme.colorScheme.primary,
            onClick = onOpenSystemSettings,
        )
    }
    state.notificationErrorMessage?.let { message ->
        MessageRow(text = message, color = MaterialTheme.colorScheme.error)
    }
    when (status) {
        HourByHourNotificationStatus.NOT_DETERMINED, HourByHourNotificationStatus.DISABLED ->
            SectionFooter("Pots triar què rebràs abans d’activar els avisos.")
        HourByHourNotificationStatus.UNAVAILABLE ->
            SectionFooter("Els avisos no estan disponibles en aquesta versió de l’app.")
        else -> Unit
    }
}

@Composable
private fun MessageRow(text: String, color: Color) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Icon(Icons.Filled.Warning, contentDescription = null, tint = color)
        Text(text = text, style = MaterialTheme.typography.bodyMedium, color = color)
    }
}

/**
 * The app and its version. It hides the secret gesture: seven quick taps show or
 * hide Hora a Hora and Agenda, without the ripple that would give it away.
 * [onSecretTap] returns whether the sections now show, or null if nothing changed.
 */
@Composable
private fun VersionRow(configuration: SettingsConfiguration, onSecretTap: () -> Boolean?) {
    var message by remember { mutableStateOf<String?>(null) }
    val currentOnSecretTap by rememberUpdatedState(onSecretTap)
    val haptics = LocalHapticFeedback.current
    LaunchedEffect(message) {
        if (message != null) {
            delay(2_000)
            message = null
        }
    }
    ListRow(
        title = configuration.appName,
        subtitle = message ?: configuration.versionAndBuild,
        leadingIcon = Icons.Outlined.Info,
        modifier = Modifier
            .semantics(mergeDescendants = true) {}
            .pointerInput(Unit) {
                detectTapGestures {
                    val shows = currentOnSecretTap() ?: return@detectTapGestures
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                    message = if (shows) "S'han activat Hora a Hora i Agenda" else "S'han amagat Hora a Hora i Agenda"
                }
            },
    )
}

/** Copies the identifier support asks for; confirms it for two seconds. */
@Composable
private fun CopyIdentifierRow(identifier: String, onCopy: (String) -> Unit) {
    var wasCopied by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(wasCopied) {
        if (wasCopied) {
            delay(2_000)
            wasCopied = false
        }
    }
    ListItem(
        headlineContent = { Text(if (wasCopied) "Identificador copiat" else "Copia l'identificador") },
        modifier = Modifier
            .fillMaxWidth()
            .clickable {
                onCopy(identifier)
                wasCopied = true
            }
            .clearAndSetSemantics {
                role = Role.Button
                contentDescription = if (wasCopied) "Identificador tècnic copiat" else "Copia l'identificador tècnic complet"
                stateDescription = identifier
            },
        supportingContent = {
            Text(
                text = identifier,
                style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
                maxLines = 2,
            )
        },
        leadingContent = {
            Icon(
                imageVector = if (wasCopied) Icons.Filled.CheckCircle else Icons.Outlined.ContentCopy,
                contentDescription = null,
                tint = if (wasCopied) CastellsTheme.colors.success else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        },
        colors = ListItemDefaults.colors(containerColor = Color.Transparent),
    )
}
