plugins {
    id("castells.jvm.library")
    id("castells.kotlin.serialization")
}

dependencies {
    api(projects.core.domain)
    api(projects.core.network)
    api(projects.core.database)
    implementation(libs.kotlinx.coroutines.core)

    testImplementation(libs.sqldelight.sqlite.driver)
}
