plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.internalsettings.ui"
}

// Only the internal app shows these settings, inside Ajustos, which the public app shares.
dependencies {
    api(projects.feature.internalsettings.presentation)
    api(projects.feature.settings.ui)
}
