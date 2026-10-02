package com.ahuguet.castellsenvena

import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.currentStateAsState
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.navigation.CastellsApp
import com.ahuguet.castellsenvena.platform.AndroidAppLinks

/**
 * The app's only activity. It shows the app in its theme, with the system's choice to remove
 * animations, read again every time the activity comes to the foreground.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val container = (application as CastellsApplication).container
        splashScreen.setKeepOnScreenCondition { container.startupGate.keepsLaunchScreen() }

        setContent {
            val lifecycleState by lifecycle.currentStateAsState()
            val isInForeground = lifecycleState.isAtLeast(Lifecycle.State.STARTED)
            val links = remember { AndroidAppLinks(this) }
            val reduceMotion = remember(isInForeground) { animationsAreOff() }

            CastellsTheme {
                CompositionLocalProvider(LocalReduceMotion provides reduceMotion) {
                    CastellsApp(models = container.models, links = links)
                }
            }
        }
    }

    /** "Remove animations" in the accessibility settings sets the animator scale to 0. */
    private fun animationsAreOff(): Boolean =
        Settings.Global.getFloat(contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
}
