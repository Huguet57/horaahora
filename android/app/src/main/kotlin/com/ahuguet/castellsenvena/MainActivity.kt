package com.ahuguet.castellsenvena

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.currentStateAsState
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.di.AppContainer
import com.ahuguet.castellsenvena.navigation.CastellsApp
import com.ahuguet.castellsenvena.notifications.HourByHourNotifications
import com.ahuguet.castellsenvena.platform.AndroidAppLinks
import kotlinx.coroutines.flow.MutableStateFlow

class MainActivity : ComponentActivity() {
    private val container: AppContainer
        get() = (application as CastellsApplication).container

    private val permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        container.notificationPermissionRequester.onResult(granted)
    }

    /** A page from a tapped notification, waiting to be opened. */
    private val pendingLink = MutableStateFlow<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val container = container
        splashScreen.setKeepOnScreenCondition { container.startupGate.keepsLaunchScreen() }
        container.notificationPermissionRequester.attach(permissionLauncher)
        // A recreated activity already opened the link of its intent.
        if (savedInstanceState == null) takeLink(intent)

        setContent {
            val lifecycleState by lifecycle.currentStateAsState()
            val isInForeground = lifecycleState.isAtLeast(Lifecycle.State.STARTED)
            val link by pendingLink.collectAsState()
            val links = remember { AndroidAppLinks(this) }
            val reduceMotion = remember(isInForeground) { animationsAreOff() }

            CastellsTheme {
                CompositionLocalProvider(LocalReduceMotion provides reduceMotion) {
                    CastellsApp(
                        models = container.models,
                        links = links,
                        isInForeground = isInForeground,
                        pendingLink = link,
                        onPendingLinkOpened = { pendingLink.value = null },
                    )
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        takeLink(intent)
    }

    override fun onDestroy() {
        container.notificationPermissionRequester.detach(permissionLauncher)
        super.onDestroy()
    }

    private fun takeLink(intent: Intent?) {
        val url = intent?.getStringExtra(HourByHourNotifications.URL_EXTRA) ?: return
        intent.removeExtra(HourByHourNotifications.URL_EXTRA)
        pendingLink.value = url
    }

    /** "Remove animations" in the accessibility settings sets the animator scale to 0. */
    private fun animationsAreOff(): Boolean =
        Settings.Global.getFloat(contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
}
