package com.ahuguet.castellsenvena.feature.internalsettings.ui

import androidx.compose.foundation.selection.selectable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.HourByHourNotificationStatus
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSettingsState
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.settingsDescription
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.settingsTitle
import com.ahuguet.castellsenvena.feature.settings.ui.SettingsScaffold

/** Which news the notifications bring, and the groups they follow. */
@Composable
internal fun NotificationInterestScreen(
    state: InternalSettingsState,
    hasFollowedGroups: Boolean,
    onSelect: (NotificationInterestLevel) -> Unit,
    onChooseGroups: () -> Unit,
    onBack: () -> Unit,
) {
    val isEnabled = state.notificationStatus != HourByHourNotificationStatus.LOADING
    SettingsScaffold(title = "Notícies", onBack = onBack) {
        SectionHeader("Quines notícies vols rebre?")
        for (level in NotificationInterestLevel.entries) {
            val isSelected = state.minimumInterest == level
            ListItem(
                headlineContent = { Text(level.settingsTitle) },
                modifier = Modifier
                    .selectable(
                        selected = isSelected,
                        enabled = isEnabled,
                        role = Role.RadioButton,
                        onClick = { onSelect(level) },
                    )
                    .alpha(if (isEnabled) 1f else 0.38f),
                supportingContent = { Text(level.settingsDescription) },
                trailingContent = {
                    Icon(
                        imageVector = Icons.Filled.Check,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.alpha(if (isSelected) 1f else 0f),
                    )
                },
                colors = ListItemDefaults.colors(containerColor = Color.Transparent),
            )
        }

        SectionHeader("Les teves colles")
        ListRow(
            title = "Tria les colles a l’Agenda",
            onClickLabel = "Obre el selector de colles de l’Agenda",
            onClick = onChooseGroups,
        )
        SectionFooter(
            if (hasFollowedGroups) {
                "Fem servir les mateixes colles que segueixes a l’Agenda."
            } else {
                "Tria les teves colles per personalitzar els avisos. Ara es té en compte l’actualitat general."
            },
        )
    }
}
