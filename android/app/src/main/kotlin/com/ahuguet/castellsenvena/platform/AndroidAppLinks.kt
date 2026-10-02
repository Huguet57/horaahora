package com.ahuguet.castellsenvena.platform

import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import androidx.browser.customtabs.CustomTabColorSchemeParams
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.content.ContextCompat
import androidx.core.net.toUri
import com.ahuguet.castellsenvena.R
import com.ahuguet.castellsenvena.navigation.AppLinks

/** Links from an activity: Custom Tabs for pages read inside the app, intents otherwise. */
class AndroidAppLinks(private val context: Context) : AppLinks {
    override fun openInApp(url: String) {
        val uri = url.toUri()
        if (uri.scheme != "https" && uri.scheme != "http") {
            openExternally(url)
            return
        }
        val colors = CustomTabColorSchemeParams.Builder()
            .setToolbarColor(ContextCompat.getColor(context, R.color.window_background))
            .build()
        val intent = CustomTabsIntent.Builder()
            .setShowTitle(true)
            .setDefaultColorSchemeParams(colors)
            .build()
        try {
            intent.launchUrl(context, uri)
        } catch (_: ActivityNotFoundException) {
            openExternally(url)
        }
    }

    /** Another app, such as the browser. */
    private fun openExternally(url: String) {
        start(Intent(Intent.ACTION_VIEW, url.toUri()))
    }

    override fun composeEmail(mailtoUrl: String) {
        start(Intent(Intent.ACTION_SENDTO, mailtoUrl.toUri()))
    }

    override fun copyToClipboard(text: String) {
        val clipboard = context.getSystemService(ClipboardManager::class.java) ?: return
        clipboard.setPrimaryClip(ClipData.newPlainText("Identificador tècnic", text))
    }

    private fun start(intent: Intent) {
        try {
            context.startActivity(intent)
        } catch (_: ActivityNotFoundException) {
            // No app on the device can open it.
        }
    }
}
