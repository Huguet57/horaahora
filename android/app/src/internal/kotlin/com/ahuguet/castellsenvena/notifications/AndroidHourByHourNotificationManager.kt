package com.ahuguet.castellsenvena.notifications

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import com.ahuguet.castellsenvena.core.data.notifications.NewsNotificationKeys
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.internaldata.notifications.NotificationPreferenceStore
import com.ahuguet.castellsenvena.core.internaldata.notifications.PushSubscriptionCoordinator
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.HourByHourNotificationManaging
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.HourByHourNotificationStatus

/**
 * News notifications on Android: the system permission, the user's choice in
 * Ajustos, the Firebase token and the backend subscription.
 *
 * Android 13 and later ask for the permission the first time the user turns
 * the notifications on. Earlier versions allow notifications by default.
 */
class AndroidHourByHourNotificationManager(
    private val context: Context,
    private val store: KeyValueStore,
    private val pushSubscriptionCoordinator: PushSubscriptionCoordinator,
    private val preferenceStore: NotificationPreferenceStore,
    private val permissionRequester: NotificationPermissionRequester,
    private val tokenProvider: PushTokenProvider,
    private val groupSelection: () -> NotificationGroupSelection,
) : HourByHourNotificationManaging {
    override val minimumInterest: NotificationInterestLevel
        get() = preferenceStore.savedValue ?: NotificationInterestLevel.HIGH

    override suspend fun currentStatus(): HourByHourNotificationStatus {
        if (!tokenProvider.isAvailable) return HourByHourNotificationStatus.UNAVAILABLE
        val status = status()
        preferenceStore.resolve(existingNotificationsEnabled = status == HourByHourNotificationStatus.ENABLED)
        when (status) {
            HourByHourNotificationStatus.ENABLED -> subscribe()
            HourByHourNotificationStatus.DISABLED, HourByHourNotificationStatus.DENIED ->
                pushSubscriptionCoordinator.setEnabled(false)
            else -> Unit
        }
        return status
    }

    override suspend fun enable(): HourByHourNotificationStatus {
        if (!tokenProvider.isAvailable) return HourByHourNotificationStatus.UNAVAILABLE
        preferenceStore.resolve(existingNotificationsEnabled = false)

        if (!HourByHourNotifications.hasPermission(context)) {
            val granted = permissionRequester.request() ?: return status()
            store.putBoolean(NewsNotificationKeys.PERMISSION_REQUESTED, true)
            if (!granted) {
                // If the user allows notifications later in the system settings, that choice counts.
                store.putBoolean(NewsNotificationKeys.ENABLED, true)
                return HourByHourNotificationStatus.DENIED
            }
        }

        store.putBoolean(NewsNotificationKeys.ENABLED, true)
        if (!HourByHourNotifications.areAllowed(context)) return HourByHourNotificationStatus.DENIED
        subscribe()
        return HourByHourNotificationStatus.ENABLED
    }

    override suspend fun disable(): HourByHourNotificationStatus {
        store.putBoolean(NewsNotificationKeys.ENABLED, false)
        pushSubscriptionCoordinator.setEnabled(false)
        tokenProvider.deleteToken()
        return if (HourByHourNotifications.areAllowed(context)) {
            HourByHourNotificationStatus.DISABLED
        } else {
            HourByHourNotificationStatus.DENIED
        }
    }

    override suspend fun openSystemSettings() {
        val notificationSettings = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
            .putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try {
            context.startActivity(notificationSettings)
        } catch (_: ActivityNotFoundException) {
            context.startActivity(
                Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            )
        }
    }

    override suspend fun setMinimumInterest(value: NotificationInterestLevel) {
        preferenceStore.save(value)
        synchronizePreferences()
    }

    override suspend fun synchronizationPending(): Boolean = pushSubscriptionCoordinator.isSynchronizationPending()

    suspend fun synchronizePreferences() {
        pushSubscriptionCoordinator.setPreferences(minimumInterest = minimumInterest, groupSelection = groupSelection())
    }

    private suspend fun subscribe() {
        synchronizePreferences()
        pushSubscriptionCoordinator.setEnabled(true)
        tokenProvider.token()?.let { pushSubscriptionCoordinator.didReceiveDeviceToken(it) }
    }

    private fun status(): HourByHourNotificationStatus {
        val choice = store.getBoolean(NewsNotificationKeys.ENABLED)
        if (HourByHourNotifications.hasPermission(context) && HourByHourNotifications.areAllowed(context)) {
            return when (choice) {
                null -> HourByHourNotificationStatus.NOT_DETERMINED
                true -> HourByHourNotificationStatus.ENABLED
                false -> HourByHourNotificationStatus.DISABLED
            }
        }
        // Android 13+ has not asked yet: turning the notifications on will.
        val canStillAsk = Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            !HourByHourNotifications.hasPermission(context) &&
            store.getBoolean(NewsNotificationKeys.PERMISSION_REQUESTED) != true
        return if (canStillAsk) HourByHourNotificationStatus.NOT_DETERMINED else HourByHourNotificationStatus.DENIED
    }
}
