package com.ahuguet.castellsenvena.feature.settings.presentation

import com.ahuguet.castellsenvena.core.common.UrlEncoding
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel

/** The app facts and links shown in Ajustos. */
data class SettingsConfiguration(
    val apiBaseUrl: String,
    val supportEmail: String,
    val appName: String,
    val appVersion: String,
    val buildNumber: String,
    val technicalIdentifier: String,
    val revistaCastellsUrl: String?,
    val elMonCastellerUrl: String?,
    val ccccAgendaUrl: String?,
    val concursCastellsUrl: String?,
) {
    val privacyUrl: String get() = apiBaseUrl.trimEnd('/') + "/privacy"

    val versionAndBuild: String get() = "Versió $appVersion ($buildNumber)"

    /**
     * A draft to support with the version and the technical identifier, which
     * the user can review and edit before sending it.
     */
    val supportEmailUrl: String
        get() = "mailto:$supportEmail" +
            "?subject=" + UrlEncoding.encodeComponent("Suport $appName") +
            "&body=" + UrlEncoding.encodeComponent(supportEmailBody)

    private val supportEmailBody: String
        get() = """
            Hola,

            Explica'ns com et podem ajudar:


            ---
            Informació tècnica (la pots revisar i editar abans d'enviar el correu)
            Versió: $appVersion ($buildNumber)
            Identificador tècnic: $technicalIdentifier
        """.trimIndent()
}

val NotificationInterestLevel.settingsTitle: String
    get() = when (this) {
        NotificationInterestLevel.LOW -> "Totes"
        NotificationInterestLevel.MEDIUM -> "Rellevants"
        NotificationInterestLevel.HIGH -> "Destacades"
    }

val NotificationInterestLevel.settingsDescription: String
    get() = when (this) {
        NotificationInterestLevel.LOW -> "Totes les notícies que publiquem."
        NotificationInterestLevel.MEDIUM -> "Totes les notícies de les teves colles i l’actualitat interessant."
        NotificationInterestLevel.HIGH -> "Notícies excepcionals i novetats interessants de les teves colles."
    }
