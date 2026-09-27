package com.ahuguet.castellsenvena

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.ahuguet.castellsenvena.navigation.CastellsApp

/** The app's only activity. It opens no links from notifications: the public app has none. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val container = (application as CastellsApplication).container
        splashScreen.setKeepOnScreenCondition { container.startupGate.keepsLaunchScreen() }

        setCastellsContent { isInForeground, links ->
            CastellsApp(models = container.models, links = links, isInForeground = isInForeground)
        }
    }
}
