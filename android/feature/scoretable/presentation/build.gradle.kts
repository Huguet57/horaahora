plugins {
    id("castells.jvm.library")
    id("castells.kotlin.serialization")
}

dependencies {
    implementation(projects.core.common)
    api(libs.kotlinx.coroutines.core)
}
