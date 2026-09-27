package com.ahuguet.castellsenvena.core.common

import kotlin.coroutines.cancellation.CancellationException

/** An error whose message can be shown to the user as it is, in Catalan. */
interface UserFacingFailure {
    val userMessage: String
}

const val UNEXPECTED_ERROR_MESSAGE = "S'ha produït un error inesperat."

/** The message to show for [this] failure. */
fun Throwable.userMessage(): String =
    (this as? UserFacingFailure)?.userMessage ?: UNEXPECTED_ERROR_MESSAGE

/**
 * Like [runCatching], but lets coroutine cancellation propagate instead of
 * reporting it as a failure.
 */
inline fun <T> runCatchingCancellable(block: () -> T): Result<T> =
    try {
        Result.success(block())
    } catch (cancellation: CancellationException) {
        throw cancellation
    } catch (failure: Exception) {
        Result.failure(failure)
    }
