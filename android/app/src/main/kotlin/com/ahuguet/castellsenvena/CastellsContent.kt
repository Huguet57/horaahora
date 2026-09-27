package com.ahuguet.castellsenvena

import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.currentStateAsState
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.navigation.AppLinks
import com.ahuguet.castellsenvena.platform.AndroidAppLinks

/**
 * Shows [content] in the app's theme, with the system's choice to remove animations and the
 * links of this activity. [content] learns whether the activity is in the foreground.
 */
fun ComponentActivity.setCastellsContent(content: @Composable (isInForeground: Boolean, links: AppLinks) -> Unit) {
    setContent {
        val lifecycleState by lifecycle.currentStateAsState()
        val isInForeground = lifecycleState.isAtLeast(Lifecycle.State.STARTED)
        val links = remember { AndroidAppLinks(this) }
        val reduceMotion = remember(isInForeground) { animationsAreOff() }

        CastellsTheme {
            CompositionLocalProvider(LocalReduceMotion provides reduceMotion) {
                content(isInForeground, links)
            }
        }
    }
}

/** "Remove animations" in the accessibility settings sets the animator scale to 0. */
private fun ComponentActivity.animationsAreOff(): Boolean =
    Settings.Global.getFloat(contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
