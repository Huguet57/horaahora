package com.ahuguet.castellsenvena.notifications

import android.Manifest
import androidx.activity.result.ActivityResultLauncher
import kotlinx.coroutines.CompletableDeferred

/**
 * Asks for the notification permission through the visible activity and
 * waits for the answer. It lives with the app, so an answer that arrives
 * after the activity is recreated still reaches the request.
 */
class NotificationPermissionRequester {
    private var launcher: ActivityResultLauncher<String>? = null
    private var pending: CompletableDeferred<Boolean>? = null

    fun attach(launcher: ActivityResultLauncher<String>) {
        this.launcher = launcher
    }

    fun detach(launcher: ActivityResultLauncher<String>) {
        if (this.launcher === launcher) this.launcher = null
    }

    fun onResult(granted: Boolean) {
        pending?.complete(granted)
        pending = null
    }

    /** Whether the user granted it, or null when no activity can ask right now. */
    suspend fun request(): Boolean? {
        pending?.let { return it.await() }
        val launcher = launcher ?: return null
        val request = CompletableDeferred<Boolean>()
        pending = request
        launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
        return request.await()
    }
}
