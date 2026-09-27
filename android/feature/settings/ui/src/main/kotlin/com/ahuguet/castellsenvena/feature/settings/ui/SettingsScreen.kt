package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsCredit

/** The key of the built-in subpage with the sources of the data. */
private const val SOURCES = "castells.settings.sources"

/**
 * Ajustos and its subpages: privacy, help and the app with the sources of its data.
 *
 * An app can add its own rows at the top ([leadingContent]) with subpages of their own,
 * opened by key and drawn by [subpage]; more sources ([additionalCredits]); and a handler
 * for taps on the version row ([onVersionTap]), which returns what the row says for a
 * moment, or null.
 */
@Composable
fun SettingsScreen(
    configuration: SettingsConfiguration,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
    modifier: Modifier = Modifier,
    additionalCredits: List<SettingsCredit> = emptyList(),
    onVersionTap: (() -> String?)? = null,
    subpage: @Composable (key: String, onBack: () -> Unit) -> Unit = { _, _ -> },
    leadingContent: @Composable ColumnScope.(openSubpage: (String) -> Unit) -> Unit = {},
) {
    var destination by rememberSaveable { mutableStateOf<String?>(null) }
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
                onOpenSources = { destination = SOURCES },
                onOpenUrl = onOpenUrl,
                onContactSupport = onContactSupport,
                onCopyIdentifier = onCopyIdentifier,
                onVersionTap = onVersionTap,
                leadingContent = { leadingContent { key -> destination = key } },
            )

            SOURCES -> SourcesAndCreditsScreen(
                credits = configuration.credits + additionalCredits,
                onOpenUrl = onOpenUrl,
                onBack = back,
            )

            else -> subpage(target, back)
        }
    }
}
