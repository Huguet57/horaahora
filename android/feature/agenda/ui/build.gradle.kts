plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.agenda.ui"
}

dependencies {
    api(projects.feature.agenda.presentation)
}
