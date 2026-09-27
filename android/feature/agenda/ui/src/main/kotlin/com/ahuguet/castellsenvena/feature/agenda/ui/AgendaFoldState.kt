package com.ahuguet.castellsenvena.feature.agenda.ui

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animate
import androidx.compose.animation.core.spring
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableFloatState
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.unit.Velocity
import com.ahuguet.castellsenvena.feature.agenda.presentation.calendar.AgendaCalendarFold

/**
 * How folded the monthly calendar is. The first stretch of the event list
 * scroll folds the month into its active week, and the list only scrolls once
 * the calendar is folded; scrolling back unfolds it after the list reaches its
 * top. A released fold settles folded or unfolded, never half-way.
 */
@Stable
internal class AgendaFoldState(
    private val listState: LazyListState,
    private val storedProgress: MutableFloatState,
    private val reduceMotion: Boolean,
) {
    /** The scroll travel, in pixels, that folds the visible month. */
    var foldDistance: Float = 1f

    /** From 0, the whole month, to 1, only the active week. */
    var progress: Float
        get() = storedProgress.floatValue
        private set(value) {
            storedProgress.floatValue = value
        }

    /** What the calendar draws: with reduced motion it switches between the two states. */
    val displayedProgress: Float
        get() = AgendaCalendarFold.effectiveProgress(progress, reduceMotion)

    val isCollapsed: Boolean by derivedStateOf { AgendaCalendarFold.snapsCollapsed(displayedProgress) }

    /** The month pager gives way to the week pager once nothing but the active week is left. */
    val isFullyFolded: Boolean by derivedStateOf { displayedProgress >= 0.999f }

    val nestedScrollConnection: NestedScrollConnection = object : NestedScrollConnection {
        override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset =
            if (available.y < 0f) Offset(0f, fold(available.y)) else Offset.Zero

        override fun onPostScroll(consumed: Offset, available: Offset, source: NestedScrollSource): Offset =
            if (available.y > 0f) Offset(0f, fold(available.y)) else Offset.Zero

        override suspend fun onPostFling(consumed: Velocity, available: Velocity): Velocity {
            settle()
            return Velocity.Zero
        }
    }

    /** Folds for an upward delta and unfolds for a downward one; returns the part it used. */
    private fun fold(delta: Float): Float {
        val distance = foldDistance
        if (distance <= 0f) return 0f
        val previous = progress
        val next = (previous - delta / distance).coerceIn(0f, 1f)
        progress = next
        return (previous - next) * distance
    }

    suspend fun settle() {
        val target = AgendaCalendarFold.restingProgress(progress)
        if (target != progress) animateTo(target)
    }

    /** The header button: unfolding also goes back to the first event of the day. */
    suspend fun toggle() {
        if (AgendaCalendarFold.snapsCollapsed(progress)) {
            listState.scrollToItem(0)
            animateTo(0f)
        } else {
            animateTo(1f)
        }
    }

    /** The whole month and the first event again, without animating. */
    suspend fun reset() {
        // Taking the list scroll also stops a running fold animation.
        listState.scrollToItem(0)
        progress = 0f
    }

    private suspend fun animateTo(target: Float) {
        // Holding the list scroll lets a new drag interrupt the animation.
        listState.scroll {
            if (reduceMotion) {
                progress = target
            } else {
                animate(
                    initialValue = progress,
                    targetValue = target,
                    animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
                ) { value, _ -> progress = value }
            }
        }
    }
}

@Composable
internal fun rememberAgendaFoldState(
    listState: LazyListState,
    foldDistance: Float,
    reduceMotion: Boolean,
): AgendaFoldState {
    val progress = rememberSaveable { mutableFloatStateOf(0f) }
    val state = remember(listState, progress, reduceMotion) { AgendaFoldState(listState, progress, reduceMotion) }
    SideEffect { state.foldDistance = foldDistance }
    return state
}
