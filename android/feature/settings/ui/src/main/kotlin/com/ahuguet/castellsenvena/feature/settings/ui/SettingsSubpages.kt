package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
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
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.semantics.Role
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
        Text(
            text = "Quines notícies vols rebre?",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(start = 32.dp, end = 32.dp, top = 16.dp, bottom = 12.dp),
        )
        GroupedCard {
            val levels = NotificationInterestLevel.entries
            levels.forEachIndexed { index, level ->
                val isSelected = state.minimumInterest == level
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .selectable(
                            selected = isSelected,
                            enabled = isEnabled,
                            role = Role.RadioButton,
                            onClick = { onSelect(level) },
                        )
                        .alpha(if (isEnabled) 1f else 0.38f)
                        .padding(horizontal = 16.dp, vertical = 14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        Text(level.settingsTitle, style = MaterialTheme.typography.bodyLarge)
                        Text(
                            text = level.settingsDescription,
                            style = MaterialTheme.typography.bodyMedium,
                            color = CastellsTheme.colors.secondaryText,
                        )
                    }
                    Icon(
                        imageVector = Icons.Filled.Check,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.alpha(if (isSelected) 1f else 0f),
                    )
                }
                if (index < levels.lastIndex) GroupedDivider()
            }
        }

        GroupedSectionHeader("Les teves colles")
        GroupedCard {
            GroupedRow(
                title = "Tria les colles a l’Agenda",
                onClickLabel = "Obre el selector de colles de l’Agenda",
                onClick = onChooseGroups,
                trailing = { DisclosureIcon() },
            )
        }
        GroupedSectionFooter(
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
    onOpenUrl: (String) -> Unit,
    onBack: () -> Unit,
) {
    val credits = listOf(
        Triple("Revista Castells", "Font de l'Hora a Hora", configuration.revistaCastellsUrl),
        Triple(
            "El Món Casteller",
            "Notícies, opinió, entrevistes i cròniques de l'Hora a Hora",
            configuration.elMonCastellerUrl,
        ),
        Triple("Coordinadora de Colles Castelleres de Catalunya (CCCC)", "Font de l'Agenda", configuration.ccccAgendaUrl),
        Triple("Taula oficial del Concurs de Castells 2026", "Font de la Calculadora", configuration.concursCastellsUrl),
    )
    SettingsScaffold(title = "Fonts i crèdits", onBack = onBack) {
        Spacer(Modifier.height(16.dp))
        GroupedCard {
            credits.forEachIndexed { index, (name, detail, url) ->
                GroupedRow(
                    title = name,
                    subtitle = detail,
                    onClick = url?.let { { onOpenUrl(it) } },
                    trailing = if (url != null) {
                        { ExternalLinkIcon() }
                    } else {
                        null
                    },
                )
                if (index < credits.lastIndex) GroupedDivider()
            }
        }
        GroupedSectionFooter(
            "Aquestes atribucions identifiquen les fonts de les dades i no impliquen cap col·laboració formal.",
        )
    }
}

/**
 * A grouped settings page: a large title on the root page, a back arrow on
 * the subpages. Scrolls as a whole, with room at the end.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun SettingsScaffold(
    title: String,
    largeTitle: Boolean = false,
    onBack: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val scrollBehavior = if (largeTitle) {
        TopAppBarDefaults.exitUntilCollapsedScrollBehavior()
    } else {
        TopAppBarDefaults.pinnedScrollBehavior()
    }
    val background = CastellsTheme.colors.groupedBackground
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
            if (largeTitle) {
                LargeTopAppBar(
                    title = { Text(title) },
                    navigationIcon = navigationIcon,
                    scrollBehavior = scrollBehavior,
                    colors = TopAppBarDefaults.largeTopAppBarColors(
                        containerColor = background,
                        scrolledContainerColor = background,
                    ),
                )
            } else {
                TopAppBar(
                    title = { Text(title) },
                    navigationIcon = navigationIcon,
                    scrollBehavior = scrollBehavior,
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = background,
                        scrolledContainerColor = background,
                    ),
                )
            }
        },
        containerColor = background,
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
