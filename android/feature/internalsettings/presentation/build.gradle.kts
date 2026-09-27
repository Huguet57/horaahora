plugins {
    id("castells.jvm.library")
}

// Only the internal app has these settings. They extend Ajustos, the calculator's
// settings, which the public app shares.
dependencies {
    api(projects.feature.settings.presentation)
    api(projects.core.domain)
    api(libs.kotlinx.coroutines.core)
}
