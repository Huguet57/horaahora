package com.ahuguet.castellsenvena.navigation

import androidx.activity.compose.BackHandler
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Calculate
import androidx.compose.material.icons.filled.FormatListNumbered
import androidx.compose.material.icons.filled.Settings
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import com.ahuguet.castellsenvena.core.domain.chat.ChatRepository
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import com.ahuguet.castellsenvena.feature.calculator.ui.CalculatorScreen
import com.ahuguet.castellsenvena.feature.scoretable.ui.ScoreTableScreen
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.ui.SettingsScreen
import kotlinx.coroutines.CoroutineScope

/** The sections in the order of the navigation bar. */
enum class AppSection(override val title: String, override val icon: ImageVector) : NavigationSection {
    CALCULATOR("Calculadora", Icons.Filled.Calculate),
    SCORE_TABLE("Puntuacions", Icons.Filled.FormatListNumbered),
    SETTINGS("Ajustos", Icons.Filled.Settings),
}

/** The long-lived models and settings the sections share. */
class CastellsAppModels(
    val conversationList: ConversationListViewModel,
    val chatRepository: ChatRepository,
    val settingsConfiguration: SettingsConfiguration,
    /** Outlives the screens: sends and deletions run here. */
    val actionScope: CoroutineScope,
    /** Called every time the app comes to the foreground. */
    val onForeground: () -> Unit,
)

/** The public app: Calculadora, Puntuacions and Ajustos. */
@Composable
fun CastellsApp(
    models: CastellsAppModels,
    links: AppLinks,
    isInForeground: Boolean,
    modifier: Modifier = Modifier,
) {
    var selectedSection by rememberSaveable { mutableStateOf(AppSection.CALCULATOR) }
    var isChatVisible by remember { mutableStateOf(false) }

    LaunchedEffect(isInForeground) {
        if (isInForeground) models.onForeground()
    }
    // Back from another section returns to the calculator before leaving the app.
    BackHandler(enabled = selectedSection != AppSection.CALCULATOR) {
        selectedSection = AppSection.CALCULATOR
    }

    SectionScaffold(
        sections = AppSection.entries,
        selectedSection = selectedSection,
        onSelectSection = { selectedSection = it },
        showsNavigationBar = !isChatVisible,
        modifier = modifier,
    ) { section ->
        when (section) {
            AppSection.CALCULATOR -> CalculatorScreen(
                repository = models.chatRepository,
                listModel = models.conversationList,
                actionScope = models.actionScope,
                onChatVisibilityChange = { isChatVisible = it },
            )

            AppSection.SCORE_TABLE -> ScoreTableScreen()

            AppSection.SETTINGS -> SettingsScreen(
                configuration = models.settingsConfiguration,
                onOpenUrl = links::openInApp,
                onContactSupport = links::composeEmail,
                onCopyIdentifier = links::copyToClipboard,
            )
        }
    }
}
