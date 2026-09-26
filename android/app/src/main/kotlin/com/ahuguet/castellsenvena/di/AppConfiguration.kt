package com.ahuguet.castellsenvena.di

import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration

/** The facts of this build and installation. */
data class AppConfiguration(
    val apiBaseUrl: String,
    /** `development` for debug builds and `production` for release builds, as on iOS. */
    val pushEnvironment: String,
    val appVersion: String,
    val buildNumber: String,
    val technicalIdentifier: String,
) {
    val settingsConfiguration: SettingsConfiguration
        get() = SettingsConfiguration(
            apiBaseUrl = apiBaseUrl,
            supportEmail = SUPPORT_EMAIL,
            appName = APP_NAME,
            appVersion = appVersion,
            buildNumber = buildNumber,
            technicalIdentifier = technicalIdentifier,
            revistaCastellsUrl = "https://revistacastells.cat/castells-hora-a-hora/",
            elMonCastellerUrl = "https://www.elmoncasteller.cat/",
            ccccAgendaUrl = "https://castellscat.cat/public/ca/agenda",
            // There is no official, versioned and stable URL for the 2026 table yet.
            concursCastellsUrl = null,
        )

    companion object {
        const val APP_NAME = "Castells en vena"
        const val SUPPORT_EMAIL = "tenimaletaapp@gmail.com"
        const val PUSH_PLATFORM = "android"
    }
}
