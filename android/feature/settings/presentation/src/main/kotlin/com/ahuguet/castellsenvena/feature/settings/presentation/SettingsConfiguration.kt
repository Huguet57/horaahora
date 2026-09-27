package com.ahuguet.castellsenvena.feature.settings.presentation

import com.ahuguet.castellsenvena.core.common.UrlEncoding

/** The app facts and links shown in Ajustos. */
data class SettingsConfiguration(
    val apiBaseUrl: String,
    val supportEmail: String,
    val appName: String,
    val appVersion: String,
    val buildNumber: String,
    val technicalIdentifier: String,
    val concursCastellsUrl: String?,
) {
    val privacyUrl: String get() = apiBaseUrl.trimEnd('/') + "/privacy"

    val versionAndBuild: String get() = "Versió $appVersion ($buildNumber)"

    /** The sources of the calculator and the score table. */
    val credits: List<SettingsCredit>
        get() = listOf(
            SettingsCredit(
                name = "Taula oficial del Concurs de Castells 2026",
                detail = "Font de la calculadora i de les puntuacions",
                url = concursCastellsUrl,
            ),
        )

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

/** A source of the app's data in «Fonts i crèdits», with its official page if it has one. */
data class SettingsCredit(
    val name: String,
    val detail: String,
    val url: String?,
)
