package com.ahuguet.castellsenvena.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Calculate
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.FormatListNumbered
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Settings
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaViewModel
import com.ahuguet.castellsenvena.feature.agenda.ui.AgendaScreen
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import com.ahuguet.castellsenvena.feature.calculator.ui.CalculatorScreen
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourViewModel
import com.ahuguet.castellsenvena.feature.hourbyhour.ui.HourByHourScreen
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSettingsModel
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSources
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.NotificationOnboardingAction
import com.ahuguet.castellsenvena.feature.internalsettings.ui.InternalSettingsScreen
import com.ahuguet.castellsenvena.feature.scoretable.ui.ScoreTableScreen
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import kotlinx.coroutines.CoroutineScope

/** The sections in the order of the navigation bar. */
enum class AppSection(
    override val title: String,
    override val icon: ImageVector,
    /** Shown only after the secret gesture in Ajustos. */
    val isHidden: Boolean = false,
) : NavigationSection {
    CALCULATOR("Calculadora", Icons.Filled.Calculate),
    SCORE_TABLE("Puntuacions", Icons.Filled.FormatListNumbered),
    HOUR_BY_HOUR("Hora a Hora", Icons.Filled.Schedule, isHidden = true),
    AGENDA("Agenda", Icons.Filled.CalendarMonth, isHidden = true),
    SETTINGS("Ajustos", Icons.Filled.Settings),
}

/** The long-lived models and settings the sections share. */
class CastellsAppModels(
    val hourByHour: HourByHourViewModel,
    val agenda: AgendaViewModel,
    val conversationList: ConversationListViewModel,
    val chatRepository: ChatRepository,
    val settings: InternalSettingsModel,
    val settingsConfiguration: SettingsConfiguration,
    val sources: InternalSources,
    /** Outlives the screens: sends, deletions and notification changes run here. */
    val actionScope: CoroutineScope,
)

/**
 * The internal app: Calculadora, Puntuacions and Ajustos, plus Hora a Hora and Agenda once
 * the secret gesture shows them.
 *
 * [pendingLink] comes from a tapped notification: it opens over Hora a Hora when that
 * section shows.
 */
@Composable
fun CastellsApp(
    models: CastellsAppModels,
    links: AppLinks,
    isInForeground: Boolean,
    pendingLink: String?,
    onPendingLinkOpened: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var selectedSection by rememberSaveable { mutableStateOf(AppSection.CALCULATOR) }
    var showsAgendaGroupFilter by rememberSaveable { mutableStateOf(false) }
    var isChatVisible by remember { mutableStateOf(false) }
    val settingsState by models.settings.state.collectAsState()
    val agendaState by models.agenda.state.collectAsState()

    LaunchedEffect(models) { models.agenda.preloadFromCache() }
    LaunchedEffect(isInForeground) {
        // Permissions may have changed in the system settings meanwhile.
        if (isInForeground) models.settings.refreshNotificationStatus()
    }
    LaunchedEffect(isInForeground, selectedSection) {
        if (isInForeground && selectedSection == AppSection.HOUR_BY_HOUR) models.hourByHour.runAutoRefresh()
    }
    LaunchedEffect(pendingLink) {
        val link = pendingLink ?: return@LaunchedEffect
        if (settingsState.showsHiddenSections) selectedSection = AppSection.HOUR_BY_HOUR
        links.openInApp(link)
        onPendingLinkOpened()
    }
    LaunchedEffect(settingsState.showsHiddenSections) {
        if (!settingsState.showsHiddenSections && selectedSection.isHidden) selectedSection = AppSection.SETTINGS
    }

    SectionScaffold(
        sections = AppSection.entries.filter { settingsState.showsHiddenSections || !it.isHidden },
        homeSection = AppSection.CALCULATOR,
        selectedSection = selectedSection,
        onSelectSection = { selectedSection = it },
        showsNavigationBar = !isChatVisible,
        modifier = modifier,
    ) { section ->
        when (section) {
            AppSection.HOUR_BY_HOUR -> HourByHourScreen(
                model = models.hourByHour,
                showsNotificationOnboarding = settingsState.showsNotificationOnboarding,
                onConfigureNotifications = {
                    models.settings.handleNotificationOnboarding(NotificationOnboardingAction.CONFIGURE) {
                        selectedSection = AppSection.SETTINGS
                    }
                },
                onDismissNotificationOnboarding = {
                    models.settings.handleNotificationOnboarding(NotificationOnboardingAction.DISMISS)
                },
                onOpenLink = links::openInApp,
            )

            AppSection.AGENDA -> AgendaScreen(
                model = models.agenda,
                showsGroupFilter = showsAgendaGroupFilter,
                onShowsGroupFilterChange = { showsAgendaGroupFilter = it },
                onOpenLink = links::openExternally,
            )

            AppSection.CALCULATOR -> CalculatorScreen(
                repository = models.chatRepository,
                listModel = models.conversationList,
                actionScope = models.actionScope,
                onChatVisibilityChange = { isChatVisible = it },
            )

            AppSection.SCORE_TABLE -> ScoreTableScreen()

            AppSection.SETTINGS -> InternalSettingsScreen(
                model = models.settings,
                configuration = models.settingsConfiguration,
                sources = models.sources,
                hasFollowedGroups = agendaState.groupFilter.isActive && agendaState.groupFilter.selectedGroupCount > 0,
                actionScope = models.actionScope,
                onChooseGroups = {
                    selectedSection = AppSection.AGENDA
                    showsAgendaGroupFilter = true
                },
                onOpenUrl = links::openInApp,
                onContactSupport = links::composeEmail,
                onCopyIdentifier = links::copyToClipboard,
            )
        }
    }
}
