package com.ahuguet.castellsenvena.core.network

import java.time.Instant
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerializationException
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.Json

/** JSON as the backend writes it: snake_case keys, declared with `@SerialName`. */
internal val CastellsJson: Json = Json {
    ignoreUnknownKeys = true
    encodeDefaults = true
}

/**
 * FastAPI writes ISO 8601 dates with or without fractional seconds and offset.
 * A date without offset is UTC.
 */
internal object FlexibleInstantSerializer : KSerializer<Instant> {
    override val descriptor: SerialDescriptor =
        PrimitiveSerialDescriptor("com.ahuguet.castellsenvena.Instant", PrimitiveKind.STRING)

    override fun deserialize(decoder: Decoder): Instant = parse(decoder.decodeString())

    override fun serialize(encoder: Encoder, value: Instant) {
        encoder.encodeString(DateTimeFormatter.ISO_INSTANT.format(value))
    }

    fun parse(value: String): Instant {
        try {
            return OffsetDateTime.parse(value).toInstant()
        } catch (_: DateTimeParseException) {
        }
        try {
            return LocalDateTime.parse(value).toInstant(ZoneOffset.UTC)
        } catch (_: DateTimeParseException) {
        }
        throw SerializationException("Data ISO 8601 no vàlida: $value")
    }
}
