plugins {
    id("castells.jvm.library")
    id("castells.kotlin.serialization")
}

dependencies {
    api(projects.core.domain)
    implementation(libs.kotlinx.coroutines.core)
    api(libs.okhttp)

    testImplementation(libs.okhttp.mockwebserver)
}
