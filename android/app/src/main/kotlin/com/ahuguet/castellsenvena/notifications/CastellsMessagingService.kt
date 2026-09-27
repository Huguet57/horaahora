package com.ahuguet.castellsenvena.notifications

import com.ahuguet.castellsenvena.CastellsApplication
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.launch

/** Receives new device tokens and the notifications that arrive while the app is open. */
class CastellsMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        val container = (application as CastellsApplication).container
        container.applicationScope.launch {
            container.pushSubscriptionCoordinator.didReceiveDeviceToken(token)
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val notification = message.notification
        HourByHourNotifications.show(
            context = this,
            title = notification?.title ?: message.data["title"],
            body = notification?.body ?: message.data["body"],
            url = message.data[HourByHourNotifications.URL_EXTRA],
            tag = notification?.tag ?: message.data["collapse_id"],
        )
    }
}
