package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel

/**
 * A manual calculator to compare theoretical performances of up to four colles: the "what if"
 * scenarios and, over them, the grid of the open one. [model] is `null` when the score table
 * could not be read.
 */
@Composable
fun ComparatorScreen(model: ComparatorViewModel?, modifier: Modifier = Modifier) {
    if (model == null) {
        ContentUnavailable(icon = Icons.Filled.Warning, title = "No s'ha pogut obrir la taula", modifier = modifier)
        return
    }
    var openScenarioId by rememberSaveable { mutableStateOf<String?>(null) }
    val reduceMotion = LocalReduceMotion.current

    BackHandler(enabled = openScenarioId != null) { openScenarioId = null }

    AnimatedContent(
        targetState = openScenarioId,
        modifier = modifier,
        transitionSpec = {
            when {
                reduceMotion -> EnterTransition.None togetherWith ExitTransition.None
                targetState != null -> (slideInHorizontally { it } togetherWith slideOutHorizontally { -it / 4 } + fadeOut())
                    .apply { targetContentZIndex = 1f }
                else -> (slideInHorizontally { -it / 4 } togetherWith slideOutHorizontally { it })
                    .apply { targetContentZIndex = -1f }
            }
        },
        label = "comparator",
    ) { scenarioId ->
        if (scenarioId == null) {
            ComparatorScenarioList(
                model = model,
                onOpen = { id ->
                    model.show(id)
                    openScenarioId = id
                },
            )
        } else {
            ComparatorScenarioScreen(model = model, onBack = { openScenarioId = null })
        }
    }
}
