plugins {
    id("castells.android.library")
    id("castells.android.compose")
}

android {
    namespace = "com.ahuguet.castellsenvena.core.designsystem"
}

dependencies {
    implementation(libs.androidx.compose.material.icons.extended)
}
