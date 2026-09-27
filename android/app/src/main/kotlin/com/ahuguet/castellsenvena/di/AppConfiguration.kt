package com.ahuguet.castellsenvena.di

import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration

/** The facts of this build and installation. */
data class AppConfiguration(
    val apiBaseUrl: String,
    /**
     * `development` for debug builds and `production` for release builds, as on iOS: where the
     * internal app subscribes to news notifications, and where the public app unsubscribes the
     * ones an earlier version turned on.
     */
    val pushEnvironment: String,
    /** The name on the launcher, which tells the public app and the internal one apart. */
    val appName: String,
    val appVersion: String,
    val buildNumber: String,
    val technicalIdentifier: String,
    /**
     * `com.ahuguet.castellsenvena`, or `com.ahuguet.castellsenvena.internal` in the internal
     * app: the backend files push subscriptions under it.
     */
    val applicationId: String,
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
        const val PUSH_PLATFORM = "android"
    }
}
