package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ExternalLinkIcon
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.feature.settings.presentation.HourByHourNotificationStatus
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsState
import com.ahuguet.castellsenvena.feature.settings.presentation.settingsDescription
import com.ahuguet.castellsenvena.feature.settings.presentation.settingsTitle

/** Which news the notifications bring, and the groups they follow. */
@Composable
internal fun NotificationInterestScreen(
    state: SettingsState,
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

/** Where the data comes from. */
@Composable
internal fun SourcesAndCreditsScreen(
    configuration: SettingsConfiguration,
    showsHiddenSections: Boolean,
    onOpenUrl: (String) -> Unit,
    onBack: () -> Unit,
) {
    val credits = buildList {
        add(
            Triple(
                "Taula oficial del Concurs de Castells 2026",
                "Font de la calculadora i de les puntuacions",
                configuration.concursCastellsUrl,
            ),
        )
        if (showsHiddenSections) {
            add(Triple("Revista Castells", "Font de l'Hora a Hora", configuration.revistaCastellsUrl))
            add(
                Triple(
                    "El Món Casteller",
                    "Notícies, opinió, entrevistes i cròniques de l'Hora a Hora",
                    configuration.elMonCastellerUrl,
                ),
            )
            add(
                Triple(
                    "Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                    "Font de l'Agenda",
                    configuration.ccccAgendaUrl,
                ),
            )
        }
    }
    SettingsScaffold(title = "Fonts i crèdits", onBack = onBack) {
        Spacer(Modifier.height(8.dp))
        for ((name, detail, url) in credits) {
            ListRow(
                title = name,
                subtitle = detail,
                onClick = url?.let { { onOpenUrl(it) } },
                trailing = if (url != null) {
                    { ExternalLinkIcon() }
                } else {
                    null
                },
            )
        }
        SectionFooter(
            "Aquestes atribucions identifiquen les fonts de les dades i no impliquen cap col·laboració formal.",
        )
    }
}

/**
 * A settings page under a top app bar, with a back arrow on the subpages.
 * Scrolls as a whole, with room at the end.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun SettingsScaffold(
    title: String,
    onBack: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()
    val navigationIcon: @Composable () -> Unit = {
        if (onBack != null) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Enrere")
            }
        }
    }
    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            TopAppBar(title = { Text(title) }, navigationIcon = navigationIcon, scrollBehavior = scrollBehavior)
        },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(PaddingValues(bottom = 32.dp)),
            content = content,
        )
    }
}
