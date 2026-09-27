package com.ahuguet.castellsenvena.core.network

import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.DeserializationStrategy
import kotlinx.serialization.SerializationException
import kotlinx.serialization.SerializationStrategy
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response

/**
 * The HTTP client of the Castells backend. The remote services build on it: those both apps
 * use are in this module, and those of the internal app's sections in :core:internaldata.
 */
class ApiClient(
    baseUrl: String,
    private val httpClient: OkHttpClient = defaultHttpClient(),
) {
    private val baseUrl: HttpUrl = baseUrl.toHttpUrl()
    private val json: Json = CastellsJson

    suspend fun <T> get(
        path: String,
        query: List<Pair<String, String>> = emptyList(),
        deserializer: DeserializationStrategy<T>,
    ): T {
        val request = Request.Builder().url(url(path, query)).get().build()
        return decode(execute(request), deserializer)
    }

    suspend fun <B, T> post(
        path: String,
        body: B,
        serializer: SerializationStrategy<B>,
        deserializer: DeserializationStrategy<T>,
    ): T {
        val request = Request.Builder()
            .url(url(path))
            .post(json.encodeToString(serializer, body).toRequestBody(JSON_MEDIA_TYPE))
            .build()
        return decode(execute(request), deserializer)
    }

    suspend fun <B> put(path: String, body: B, serializer: SerializationStrategy<B>) {
        val request = Request.Builder()
            .url(url(path))
            .put(json.encodeToString(serializer, body).toRequestBody(JSON_MEDIA_TYPE))
            .build()
        execute(request)
    }

    suspend fun delete(path: String, query: List<Pair<String, String>> = emptyList()) {
        val request = Request.Builder().url(url(path, query)).delete().build()
        execute(request)
    }

    private fun url(path: String, query: List<Pair<String, String>> = emptyList()): HttpUrl {
        val builder = baseUrl.newBuilder().addPathSegments(path.trimStart('/'))
        for ((name, value) in query) builder.addQueryParameter(name, value)
        return builder.build()
    }

    private suspend fun execute(request: Request): String {
        val result = try {
            httpClient.newCall(request).await()
        } catch (failure: IOException) {
            throw ApiException.Network(failure)
        }
        if (result.statusCode !in 200..299) {
            throw ApiException.Http(result.statusCode, errorDetail(result.body))
        }
        return result.body
    }

    private fun <T> decode(body: String, deserializer: DeserializationStrategy<T>): T =
        try {
            json.decodeFromString(deserializer, body)
        } catch (failure: SerializationException) {
            throw ApiException.InvalidResponse(failure)
        } catch (failure: IllegalArgumentException) {
            throw ApiException.InvalidResponse(failure)
        }

    /** FastAPI errors carry a `detail` string; validation errors carry a list instead. */
    private fun errorDetail(body: String): String? =
        try {
            val detail = (json.parseToJsonElement(body) as? JsonObject)?.get("detail")
            (detail as? JsonPrimitive)?.takeIf { it.isString }?.content
        } catch (_: SerializationException) {
            null
        }

    private class HttpResult(val statusCode: Int, val body: String)

    /** Runs the call on OkHttp's dispatcher and cancels it with the coroutine. */
    private suspend fun Call.await(): HttpResult = suspendCancellableCoroutine { continuation ->
        continuation.invokeOnCancellation { cancel() }
        enqueue(
            object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    continuation.resumeWithException(e)
                }

                override fun onResponse(call: Call, response: Response) {
                    val result = try {
                        response.use { HttpResult(it.code, it.body.string()) }
                    } catch (failure: IOException) {
                        continuation.resumeWithException(failure)
                        return
                    }
                    continuation.resume(result)
                }
            },
        )
    }

    companion object {
        private val JSON_MEDIA_TYPE = "application/json".toMediaType()

        /** The calculator waits for a language model, so reads get a generous timeout. */
        fun defaultHttpClient(): OkHttpClient = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
}
