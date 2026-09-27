package com.ahuguet.castellsenvena

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.ahuguet.castellsenvena.di.AppContainer
import com.ahuguet.castellsenvena.navigation.CastellsApp
import com.ahuguet.castellsenvena.notifications.HourByHourNotifications
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

        setCastellsContent { isInForeground, links ->
            val link by pendingLink.collectAsState()
            CastellsApp(
                models = container.models,
                links = links,
                isInForeground = isInForeground,
                pendingLink = link,
                onPendingLinkOpened = { pendingLink.value = null },
            )
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
}
