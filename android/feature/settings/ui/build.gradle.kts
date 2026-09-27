plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.settings.ui"
}

dependencies {
    api(projects.feature.settings.presentation)
}
