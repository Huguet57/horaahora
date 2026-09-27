plugins {
    id("castells.jvm.library")
}

dependencies {
    api(projects.core.domain)
    api(libs.kotlinx.coroutines.core)
}
