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
import androidx.compose.runtime.collectAsState
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
    val state by model.state.collectAsState()
    var savedScenarioId by rememberSaveable { mutableStateOf<String?>(null) }
    // The scenario that was open may be gone when the screen comes back after the process died:
    // an untouched first scenario loads as none, and the list says so.
    val openScenarioId = savedScenarioId?.takeIf { id -> state.scenarios.any { it.id == id } }
    val reduceMotion = LocalReduceMotion.current

    BackHandler(enabled = openScenarioId != null) { savedScenarioId = null }

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
                    savedScenarioId = id
                },
            )
        } else {
            ComparatorScenarioScreen(model = model, onBack = { savedScenarioId = null })
        }
    }
}
