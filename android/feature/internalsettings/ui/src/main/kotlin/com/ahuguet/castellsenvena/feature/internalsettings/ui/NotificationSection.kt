package com.ahuguet.castellsenvena.feature.internalsettings.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.HourByHourNotificationStatus
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSettingsState
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.settingsTitle

/** The news notifications at the top of Ajustos: on or off, and which news they bring. */
@Composable
internal fun NotificationSection(
    state: InternalSettingsState,
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
