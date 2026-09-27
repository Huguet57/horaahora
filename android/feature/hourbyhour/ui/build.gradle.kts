plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.hourbyhour.ui"
}

dependencies {
    api(projects.feature.hourbyhour.presentation)
}
