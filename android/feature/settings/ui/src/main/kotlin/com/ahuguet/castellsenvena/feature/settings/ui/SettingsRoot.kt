package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.DisclosureIcon
import com.ahuguet.castellsenvena.core.designsystem.component.ExternalLinkIcon
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedCard
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedDivider
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedRow
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedSectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedSectionHeader
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
) {
    SettingsScaffold(title = "Ajustos", largeTitle = true) {
        NotificationSection(
            state = state,
            onEnabledChange = onNotificationsEnabledChange,
            onOpenInterest = onOpenNotificationInterest,
            onOpenSystemSettings = onOpenSystemSettings,
        )

        GroupedSectionHeader("Privacitat i dades")
        GroupedCard {
            GroupedRow(
                title = "Política de privacitat",
                leadingIcon = Icons.Outlined.FrontHand,
                onClick = { onOpenUrl(configuration.privacyUrl) },
                trailing = { ExternalLinkIcon() },
            )
        }

        GroupedSectionHeader("Ajuda")
        GroupedCard {
            GroupedRow(
                title = "Contacta amb suport",
                leadingIcon = Icons.Outlined.Email,
                onClick = { onContactSupport(configuration.supportEmailUrl) },
                trailing = { ExternalLinkIcon() },
            )
            GroupedDivider(startIndent = 54.dp)
            CopyIdentifierRow(identifier = configuration.technicalIdentifier, onCopy = onCopyIdentifier)
        }

        GroupedSectionHeader("Sobre ${configuration.appName}")
        GroupedCard {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .semantics(mergeDescendants = true) {}
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                Text(configuration.appName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text(
                    text = configuration.versionAndBuild,
                    style = MaterialTheme.typography.bodyMedium,
                    color = CastellsTheme.colors.secondaryText,
                )
            }
            GroupedDivider()
            GroupedRow(
                title = "Fonts i crèdits",
                leadingIcon = Icons.AutoMirrored.Outlined.MenuBook,
                onClick = onOpenSources,
                trailing = { DisclosureIcon() },
            )
        }
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

    GroupedSectionHeader("Notificacions")
    GroupedCard {
        GroupedRow(
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
        GroupedDivider(startIndent = 54.dp)
        GroupedRow(
            title = "Quines notícies?",
            subtitle = state.minimumInterest.settingsTitle,
            enabled = status != HourByHourNotificationStatus.LOADING,
            onClick = onOpenInterest,
            trailing = { DisclosureIcon() },
        )
        if (status == HourByHourNotificationStatus.DENIED) {
            GroupedDivider()
            MessageRow(text = "Bloquejades per Android", color = CastellsTheme.colors.warning)
            GroupedRow(
                title = "Obre els ajustos del sistema",
                titleColor = MaterialTheme.colorScheme.primary,
                onClick = onOpenSystemSettings,
            )
        }
        state.notificationErrorMessage?.let { message ->
            GroupedDivider()
            MessageRow(text = message, color = MaterialTheme.colorScheme.error)
        }
    }
    when (status) {
        HourByHourNotificationStatus.NOT_DETERMINED, HourByHourNotificationStatus.DISABLED ->
            GroupedSectionFooter("Pots triar què rebràs abans d’activar els avisos.")
        HourByHourNotificationStatus.UNAVAILABLE ->
            GroupedSectionFooter("Els avisos no estan disponibles en aquesta versió de l’app.")
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
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(Icons.Filled.Warning, contentDescription = null, tint = color)
        Text(text = text, style = MaterialTheme.typography.bodyMedium, color = color)
    }
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
    Row(
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
            }
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Icon(
            imageVector = if (wasCopied) Icons.Filled.CheckCircle else Icons.Outlined.ContentCopy,
            contentDescription = null,
            tint = if (wasCopied) CastellsTheme.colors.success else MaterialTheme.colorScheme.primary,
        )
        Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(
                text = if (wasCopied) "Identificador copiat" else "Copia l'identificador",
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(
                text = identifier,
                style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
                color = CastellsTheme.colors.secondaryText,
                maxLines = 2,
            )
        }
    }
}
