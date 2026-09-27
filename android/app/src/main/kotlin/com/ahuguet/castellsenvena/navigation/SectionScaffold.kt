package com.ahuguet.castellsenvena.navigation

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion

/** A section of the navigation bar. */
interface NavigationSection {
    val title: String
    val icon: ImageVector
}

/**
 * [sections] behind a bottom navigation bar, which hides while [showsNavigationBar] is
 * false. The selected section keeps its scroll and navigation state while another one is
 * shown.
 */
@Composable
fun <S> SectionScaffold(
    sections: List<S>,
    selectedSection: S,
    onSelectSection: (S) -> Unit,
    showsNavigationBar: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable (S) -> Unit,
) where S : Enum<S>, S : NavigationSection {
    val sectionStates = rememberSaveableStateHolder()
    val reduceMotion = LocalReduceMotion.current

    Scaffold(
        modifier = modifier,
        bottomBar = {
            AnimatedVisibility(
                visible = showsNavigationBar,
                enter = if (reduceMotion) EnterTransition.None else expandVertically(),
                exit = if (reduceMotion) ExitTransition.None else shrinkVertically(),
            ) {
                NavigationBar {
                    for (section in sections) {
                        NavigationBarItem(
                            selected = section == selectedSection,
                            onClick = { onSelectSection(section) },
                            icon = { Icon(section.icon, contentDescription = null) },
                            label = { Text(section.title) },
                        )
                    }
                }
            }
        },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .consumeWindowInsets(padding),
        ) {
            sectionStates.SaveableStateProvider(selectedSection) {
                content(selectedSection)
            }
        }
    }
}
