package com.ahuguet.castellsenvena.feature.settings.presentation

import com.ahuguet.castellsenvena.core.common.userMessage
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.domain.settings.HiddenSectionsPreferences
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

enum class HourByHourNotificationStatus {
    LOADING,

    /** The user has not decided yet: the Hora a Hora onboarding card is shown. */
    NOT_DETERMINED,
    ENABLED,
    DISABLED,

    /** Blocked in the system settings. */
    DENIED,

    /** This build has no push configuration (no Firebase project). */
    UNAVAILABLE,
}

/** The platform side of news notifications: permission, device token and preferences. */
interface HourByHourNotificationManaging {
    val minimumInterest: NotificationInterestLevel
    suspend fun setMinimumInterest(value: NotificationInterestLevel)
    suspend fun synchronizationPending(): Boolean
    suspend fun currentStatus(): HourByHourNotificationStatus
    suspend fun enable(): HourByHourNotificationStatus
    suspend fun disable(): HourByHourNotificationStatus
    suspend fun openSystemSettings()
}

enum class NotificationOnboardingAction {
    CONFIGURE,
    DISMISS,
}

data class SettingsState(
    val notificationStatus: HourByHourNotificationStatus = HourByHourNotificationStatus.LOADING,
    val isUpdatingNotifications: Boolean = false,
    val notificationErrorMessage: String? = null,
    val isNotificationOnboardingDismissed: Boolean = false,
    val minimumInterest: NotificationInterestLevel = NotificationInterestLevel.HIGH,
    val isNotificationSynchronizationPending: Boolean = false,
    /** Hora a Hora, Agenda and their settings, hidden unless a secret gesture shows them. */
    val showsHiddenSections: Boolean = false,
) {
    val showsNotificationOnboarding: Boolean
        get() = notificationStatus == HourByHourNotificationStatus.NOT_DETERMINED && !isNotificationOnboardingDismissed

    val canToggleNotifications: Boolean
        get() = notificationStatus !in setOf(
            HourByHourNotificationStatus.LOADING,
            HourByHourNotificationStatus.DENIED,
            HourByHourNotificationStatus.UNAVAILABLE,
        ) && !isUpdatingNotifications
}

class SettingsModel(
    private val notificationManager: HourByHourNotificationManaging,
    notificationOnboardingDismissed: Boolean = false,
    private val persistNotificationOnboardingDismissal: (Boolean) -> Unit = {},
    private val hiddenSections: HiddenSectionsPreferences? = null,
    /** A monotonic clock, for the pauses between the taps of the secret gesture. */
    private val nowMillis: () -> Long = { System.nanoTime() / 1_000_000 },
) {
    private val mutableState = MutableStateFlow(
        SettingsState(
            isNotificationOnboardingDismissed = notificationOnboardingDismissed,
            showsHiddenSections = hiddenSections?.isUnlocked ?: false,
        ),
    )
    val state: StateFlow<SettingsState> = mutableState.asStateFlow()
    private val secretTaps = SecretTapSequence()

    suspend fun refreshNotificationStatus() {
        val status = notificationManager.currentStatus()
        mutableState.update { it.copy(notificationStatus = status) }
        hiddenSections?.let { preferences ->
            preferences.resolveDefault(notificationsEnabled = status == HourByHourNotificationStatus.ENABLED)
            mutableState.update { it.copy(showsHiddenSections = preferences.isUnlocked) }
        }
        refreshPreferences()
    }

    /**
     * Counts a tap on the version; the seventh quick one shows or hides the hidden
     * sections. Returns whether this tap changed them.
     */
    fun registerSecretTap(): Boolean {
        val preferences = hiddenSections ?: return false
        if (!secretTaps.register(nowMillis())) return false
        preferences.setUnlocked(!preferences.isUnlocked)
        mutableState.update { it.copy(showsHiddenSections = preferences.isUnlocked) }
        return true
    }

    suspend fun setMinimumInterest(value: NotificationInterestLevel) {
        mutableState.update { it.copy(minimumInterest = value) }
        notificationManager.setMinimumInterest(value)
        refreshPreferences()
    }

    fun setNotificationSynchronizationPending(pending: Boolean) {
        mutableState.update { it.copy(isNotificationSynchronizationPending = pending) }
    }

    suspend fun setHourByHourNotificationsEnabled(enabled: Boolean) {
        if (mutableState.value.isUpdatingNotifications) return
        mutableState.update { it.copy(isUpdatingNotifications = true, notificationErrorMessage = null) }
        try {
            val status = if (enabled) notificationManager.enable() else notificationManager.disable()
            mutableState.update { it.copy(notificationStatus = status) }
            refreshPreferences()
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (failure: Exception) {
            mutableState.update { it.copy(notificationErrorMessage = failure.userMessage()) }
        } finally {
            mutableState.update { it.copy(isUpdatingNotifications = false) }
        }
    }

    suspend fun openSystemSettings() {
        notificationManager.openSystemSettings()
    }

    /** "Configura-ho" opens the settings and keeps the card; "Ara no" hides it for good. */
    fun handleNotificationOnboarding(action: NotificationOnboardingAction, openSettings: () -> Unit = {}) {
        when (action) {
            NotificationOnboardingAction.CONFIGURE -> openSettings()
            NotificationOnboardingAction.DISMISS -> {
                mutableState.update { it.copy(isNotificationOnboardingDismissed = true) }
                persistNotificationOnboardingDismissal(true)
            }
        }
    }

    private suspend fun refreshPreferences() {
        val minimumInterest = notificationManager.minimumInterest
        val pending = notificationManager.synchronizationPending()
        mutableState.update {
            it.copy(minimumInterest = minimumInterest, isNotificationSynchronizationPending = pending)
        }
    }

    internal fun setNotificationStatusForTesting(status: HourByHourNotificationStatus) {
        mutableState.update { it.copy(notificationStatus = status) }
    }
}
