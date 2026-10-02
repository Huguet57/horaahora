package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration

/** Ajustos and its subpage: privacy, help and the app with the sources of its data. */
@Composable
fun SettingsScreen(
    configuration: SettingsConfiguration,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var destination by rememberSaveable { mutableStateOf<SettingsDestination?>(null) }
    val reduceMotion = LocalReduceMotion.current
    val back: () -> Unit = { destination = null }

    BackHandler(enabled = destination != null, onBack = back)

    AnimatedContent(
        targetState = destination,
        modifier = modifier,
        transitionSpec = {
            when {
                reduceMotion -> EnterTransition.None togetherWith ExitTransition.None
                targetState != null ->
                    (slideInHorizontally { it } togetherWith slideOutHorizontally { -it / 4 } + fadeOut())
                        .apply { targetContentZIndex = 1f }
                else -> (slideInHorizontally { -it / 4 } togetherWith slideOutHorizontally { it })
                    .apply { targetContentZIndex = -1f }
            }
        },
        label = "settings",
    ) { target ->
        when (target) {
            null -> SettingsRoot(
                configuration = configuration,
                onOpenSources = { destination = SettingsDestination.SOURCES },
                onOpenUrl = onOpenUrl,
                onContactSupport = onContactSupport,
                onCopyIdentifier = onCopyIdentifier,
            )

            SettingsDestination.SOURCES -> SourcesAndCreditsScreen(
                credits = configuration.credits,
                onOpenUrl = onOpenUrl,
                onBack = back,
            )
        }
    }
}

/** The subpages of Ajustos: the sources of the data. */
private enum class SettingsDestination { SOURCES }
