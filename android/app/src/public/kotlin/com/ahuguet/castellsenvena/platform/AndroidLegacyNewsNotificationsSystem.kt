package com.ahuguet.castellsenvena.platform

import android.content.Context
import androidx.core.app.NotificationManagerCompat
import com.ahuguet.castellsenvena.R
import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsSystem

/**
 * The news notifications that earlier versions set up: their channel, «Avisos de notícies»,
 * and the notifications it still shows. The public app never shows any.
 */
class AndroidLegacyNewsNotificationsSystem(context: Context) : LegacyNewsNotificationsSystem {
    private val manager = NotificationManagerCompat.from(context)
    private val channelId = context.getString(R.string.hour_by_hour_channel_id)

    override fun hadNewsNotifications(): Boolean = manager.getNotificationChannelCompat(channelId) != null

    override fun stopShowingNewsNotifications() {
        manager.cancelAll()
        manager.deleteNotificationChannel(channelId)
    }
}
