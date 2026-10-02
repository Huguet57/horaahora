package com.ahuguet.castellsenvena.di

import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration

/** The facts of this build and installation. */
data class AppConfiguration(
    val apiBaseUrl: String,
    /** The name on the launcher. */
    val appName: String,
    val appVersion: String,
    val buildNumber: String,
    val technicalIdentifier: String,
) {
    val settingsConfiguration: SettingsConfiguration
        get() = SettingsConfiguration(
            apiBaseUrl = apiBaseUrl,
            supportEmail = SUPPORT_EMAIL,
            appName = appName,
            appVersion = appVersion,
            buildNumber = buildNumber,
            technicalIdentifier = technicalIdentifier,
            // There is no official, versioned and stable URL for the 2026 table yet.
            concursCastellsUrl = null,
        )

    companion object {
        const val SUPPORT_EMAIL = "tenimaletaapp@gmail.com"
    }
}
