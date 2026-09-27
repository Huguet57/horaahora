package com.ahuguet.castellsenvena.core.internaldata.notifications

import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRemoteService
import com.ahuguet.castellsenvena.core.network.service.PushSubscriptionRequest
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/**
 * Keeps the backend subscription in line with the local choice: enabled or
 * not, device token, interest level and followed groups.
 *
 * Callers only change the desired state. A single draining loop performs the
 * network writes, so concurrent changes are serialized and the latest wins. A
 * failed write stays pending until the next change or foreground refresh.
 */
class PushSubscriptionCoordinator(
    private val remoteService: PushSubscriptionRemoteService,
    private val installationId: String,
    private val appVersion: String,
    private val locale: String,
    private val environment: String,
    private val platform: String,
) {
    private val mutex = Mutex()
    private var desiredEnabled = false
    private var minimumInterest = NotificationInterestLevel.HIGH
    private var groupSelection = NotificationGroupSelection()
    private var currentDeviceToken: String? = null
    private var synchronizedRequest: PushSubscriptionRequest? = null
    private var isUnregistered = false
    private var isSynchronizing = false
    private var hasRequestedSynchronization = false
    private var generation = 0L

    private val pending = MutableStateFlow(false)

    /** Whether the backend still misses the latest local choice. */
    val synchronizationPending: StateFlow<Boolean> = pending.asStateFlow()

    suspend fun isSynchronizationPending(): Boolean = mutex.withLock { isPendingLocked() }

    suspend fun setEnabled(enabled: Boolean) {
        mutex.withLock {
            generation++
            desiredEnabled = enabled
            hasRequestedSynchronization = true
        }
        synchronize()
    }

    suspend fun setPreferences(
        minimumInterest: NotificationInterestLevel,
        groupSelection: NotificationGroupSelection,
    ) {
        val shouldSynchronize = mutex.withLock {
            generation++
            this.minimumInterest = minimumInterest
            this.groupSelection = groupSelection
            // Preferences stay local until notifications are enabled or disabled explicitly.
            hasRequestedSynchronization
        }
        if (shouldSynchronize) synchronize()
    }

    suspend fun didReceiveDeviceToken(token: String) {
        val shouldSynchronize = mutex.withLock {
            generation++
            currentDeviceToken = token
            hasRequestedSynchronization
        }
        if (shouldSynchronize) synchronize()
    }

    private suspend fun synchronize() {
        val ownsSynchronization = mutex.withLock {
            if (isSynchronizing) {
                false
            } else {
                isSynchronizing = true
                true
            }
        }
        if (!ownsSynchronization) return

        var lastObservedGeneration = -1L
        var runAgain = false
        try {
            lastObservedGeneration = drain()
        } finally {
            withContext(NonCancellable) {
                mutex.withLock {
                    isSynchronizing = false
                    pending.value = isPendingLocked()
                    // A change that arrived after the loop's last look was not written yet.
                    runAgain = generation != lastObservedGeneration && isPendingLocked()
                }
            }
        }
        if (runAgain) synchronize()
    }

    /** Writes until nothing is pending or a write fails; returns the generation it last saw. */
    private suspend fun drain(): Long {
        while (true) {
            val (action, observedGeneration) = mutex.withLock { nextActionLocked() to generation }
            when (action) {
                null -> return observedGeneration

                is Action.Register -> {
                    val succeeded = attempt { remoteService.register(action.request) }
                    val (proceed, seenGeneration) = mutex.withLock {
                        val proceed = if (succeeded) {
                            synchronizedRequest = action.request
                            isUnregistered = false
                            true
                        } else {
                            // Retry at once only if the desired state changed meanwhile.
                            !desiredEnabled || action.request != desiredRequestLocked()
                        }
                        proceed to generation
                    }
                    if (!proceed) return seenGeneration
                }

                Action.Unregister -> {
                    val succeeded = attempt {
                        remoteService.unregister(installationId, environment, platform)
                    }
                    val (proceed, seenGeneration) = mutex.withLock {
                        val proceed = if (succeeded) {
                            isUnregistered = true
                            synchronizedRequest = null
                            true
                        } else {
                            desiredEnabled
                        }
                        proceed to generation
                    }
                    if (!proceed) return seenGeneration
                }
            }
        }
    }

    private fun nextActionLocked(): Action? {
        if (!isPendingLocked()) return null
        if (!desiredEnabled) return Action.Unregister
        // Enabled but still waiting for a device token.
        return desiredRequestLocked()?.let(Action::Register)
    }

    private fun isPendingLocked(): Boolean {
        if (!hasRequestedSynchronization) return false
        return if (desiredEnabled) {
            val desired = desiredRequestLocked()
            desired == null || desired != synchronizedRequest
        } else {
            !isUnregistered
        }
    }

    private fun desiredRequestLocked(): PushSubscriptionRequest? =
        currentDeviceToken?.let { token ->
            PushSubscriptionRequest(
                installationId = installationId,
                deviceToken = token,
                appVersion = appVersion,
                locale = locale,
                environment = environment,
                platform = platform,
                minimumInterest = minimumInterest,
                groupSelection = groupSelection,
            )
        }

    private suspend fun attempt(write: suspend () -> Unit): Boolean =
        try {
            write()
            true
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (_: Exception) {
            false
        }

    private sealed interface Action {
        data class Register(val request: PushSubscriptionRequest) : Action
        data object Unregister : Action
    }
}
