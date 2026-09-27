package com.ahuguet.castellsenvena.notifications

import android.content.Context
import com.google.android.gms.tasks.Task
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import kotlin.coroutines.cancellation.CancellationException
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.suspendCancellableCoroutine

/** The device token news notifications are delivered to. */
interface PushTokenProvider {
    /** False when this build has no Firebase project (no google-services.json). */
    val isAvailable: Boolean

    /** Creates the token if needed; null when it cannot be obtained right now. */
    suspend fun token(): String?

    /** Forgets the token, so the device stops receiving notifications at once. */
    suspend fun deleteToken()
}

class FirebasePushTokenProvider(private val context: Context) : PushTokenProvider {
    override val isAvailable: Boolean
        get() = FirebaseApp.getApps(context).isNotEmpty()

    override suspend fun token(): String? {
        if (!isAvailable) return null
        val messaging = FirebaseMessaging.getInstance()
        // Token refreshes are only wanted while the notifications are on.
        messaging.isAutoInitEnabled = true
        return try {
            messaging.token.await()
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (_: Exception) {
            // Offline or Play services unavailable: the next foreground refresh retries.
            null
        }
    }

    override suspend fun deleteToken() {
        if (!isAvailable) return
        val messaging = FirebaseMessaging.getInstance()
        messaging.isAutoInitEnabled = false
        try {
            messaging.deleteToken().await()
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (_: Exception) {
            // The backend subscription is removed anyway.
        }
    }
}

private suspend fun <T> Task<T>.await(): T = suspendCancellableCoroutine { continuation ->
    addOnCompleteListener { task ->
        val exception = task.exception
        when {
            exception != null -> continuation.resumeWithException(exception)
            task.isCanceled -> continuation.cancel()
            else -> continuation.resume(task.result)
        }
    }
}
