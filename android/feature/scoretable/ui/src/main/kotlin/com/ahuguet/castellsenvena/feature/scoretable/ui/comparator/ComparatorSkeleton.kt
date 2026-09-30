package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.snap
import androidx.compose.animation.core.tween
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.drawOutline
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion

/** How long a fresh copy of a scenario shows as a placeholder before it reveals itself. */
internal const val DUPLICATE_SKELETON_MILLIS = 600L

/**
 * Draws a pulsing placeholder of [shape] instead of the content while [visible], keeping its
 * layout, so that a copy that looks just like its original reads as a new scenario. The content
 * fades back in when it stops.
 */
@Composable
internal fun Modifier.skeleton(visible: Boolean, shape: Shape = RoundedCornerShape(4.dp)): Modifier {
    val reduceMotion = LocalReduceMotion.current
    val cover by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = if (visible || reduceMotion) snap() else tween(durationMillis = 250),
        label = "skeleton",
    )
    if (cover == 0f) return this
    val pulse = if (visible && !reduceMotion) {
        val pulse by rememberInfiniteTransition(label = "skeleton pulse").animateFloat(
            initialValue = 0.78f,
            targetValue = 0.45f,
            animationSpec = infiniteRepeatable(tween(durationMillis = 300), RepeatMode.Reverse),
            label = "skeleton pulse",
        )
        pulse
    } else {
        0.68f
    }
    val color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f * pulse * cover)
    return this
        .drawWithContent {
            drawContent()
            drawOutline(shape.createOutline(size, layoutDirection, this), color)
        }
        .graphicsLayer { alpha = 1f - cover }
}
