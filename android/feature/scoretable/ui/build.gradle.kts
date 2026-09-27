plugins {
    id("castells.android.feature")
}

android {
    namespace = "com.ahuguet.castellsenvena.feature.scoretable.ui"
}

dependencies {
    api(projects.feature.scoretable.presentation)
}
