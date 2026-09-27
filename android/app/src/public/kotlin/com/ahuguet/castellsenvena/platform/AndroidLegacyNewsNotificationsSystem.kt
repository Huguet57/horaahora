package com.ahuguet.castellsenvena.platform

import android.content.Context
import androidx.core.app.NotificationManagerCompat
import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsSystem

/**
 * The news notifications that earlier versions set up: their channel, «Avisos de notícies»,
 * and the notifications it still shows. The public app never shows any.
 */
class AndroidLegacyNewsNotificationsSystem(context: Context) : LegacyNewsNotificationsSystem {
    private val manager = NotificationManagerCompat.from(context)

    override fun hadNewsNotifications(): Boolean = manager.getNotificationChannelCompat(CHANNEL_ID) != null

    override fun stopShowingNewsNotifications() {
        manager.cancelAll()
        manager.deleteNotificationChannel(CHANNEL_ID)
    }

    private companion object {
        /** The channel of the news notifications in earlier versions. */
        const val CHANNEL_ID = "hour_by_hour"
    }
}
