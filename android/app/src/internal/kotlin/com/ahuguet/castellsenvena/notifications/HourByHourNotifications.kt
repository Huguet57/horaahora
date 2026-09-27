package com.ahuguet.castellsenvena.notifications

import android.Manifest
import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationChannelCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.ahuguet.castellsenvena.MainActivity
import com.ahuguet.castellsenvena.R

/** The Hora a Hora notification channel and the notifications shown while the app is open. */
object HourByHourNotifications {
    /** The extra with the page a notification opens, as in the push payload. */
    const val URL_EXTRA = "url"

    fun createChannel(context: Context) {
        val channel = NotificationChannelCompat.Builder(
            context.getString(R.string.hour_by_hour_channel_id),
            NotificationManagerCompat.IMPORTANCE_HIGH,
        )
            .setName(context.getString(R.string.hour_by_hour_channel_name))
            .setDescription(context.getString(R.string.hour_by_hour_channel_description))
            .build()
        NotificationManagerCompat.from(context).createNotificationChannel(channel)
    }

    /** Whether the system lets the app show Hora a Hora notifications. */
    fun areAllowed(context: Context): Boolean {
        val manager = NotificationManagerCompat.from(context)
        if (!manager.areNotificationsEnabled()) return false
        val channel = manager.getNotificationChannelCompat(context.getString(R.string.hour_by_hour_channel_id))
        return channel == null || channel.importance != NotificationManagerCompat.IMPORTANCE_NONE
    }

    fun hasPermission(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    /**
     * Shows a news notification. While the app is in the background the system
     * shows it from the push payload instead, with the same tag and link.
     */
    @SuppressLint("MissingPermission") // Checked by hasPermission.
    fun show(context: Context, title: String?, body: String?, url: String?, tag: String?) {
        if (title.isNullOrBlank() && body.isNullOrBlank()) return
        if (!hasPermission(context) || !areAllowed(context)) return

        val intent = Intent(context, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        if (url != null) intent.putExtra(URL_EXTRA, url)
        val pendingIntent = PendingIntent.getActivity(
            context,
            (tag ?: url ?: title).hashCode(),
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification = NotificationCompat.Builder(context, context.getString(R.string.hour_by_hour_channel_id))
            .setSmallIcon(R.drawable.ic_notification)
            .setColor(ContextCompat.getColor(context, R.color.brand_red))
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()
        NotificationManagerCompat.from(context).notify(tag, 0, notification)
    }
}
