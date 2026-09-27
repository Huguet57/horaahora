package com.ahuguet.castellsenvena.core.network

import com.ahuguet.castellsenvena.core.common.UserFacingFailure
import java.io.IOException

sealed class ApiException(message: String, cause: Throwable? = null) :
    IOException(message, cause), UserFacingFailure {

    /** The request could not reach the server. */
    class Network(cause: IOException) : ApiException("Network failure: ${cause.message}", cause) {
        override val userMessage: String =
            "No s'ha pogut connectar amb el servidor. Comprova la connexió a Internet."
    }

    /** The server answered with a non-2xx status and, sometimes, a readable detail. */
    class Http(val statusCode: Int, val detail: String?) : ApiException("HTTP $statusCode: $detail") {
        override val userMessage: String = detail ?: "El servidor ha retornat l'error $statusCode."
    }

    class InvalidResponse(cause: Throwable) : ApiException("Invalid response: ${cause.message}", cause) {
        override val userMessage: String = "La resposta del servidor no és vàlida."
    }
}
