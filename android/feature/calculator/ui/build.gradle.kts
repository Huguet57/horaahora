plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.calculator.ui"
}

dependencies {
    api(projects.feature.calculator.presentation)
}
