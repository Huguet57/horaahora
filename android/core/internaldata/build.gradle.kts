plugins {
    id("castells.jvm.library")
    id("castells.kotlin.serialization")
}

// The data of the internal app's sections: Hora a Hora, Agenda, the group directory, the news
// notifications and the hidden sections. Only the internal flavor of :app depends on it; the
// local database schema, tables of these sections included, stays in :core:database.
dependencies {
    api(projects.core.data)
    implementation(libs.kotlinx.coroutines.core)

    testImplementation(libs.okhttp.mockwebserver)
    testImplementation(libs.sqldelight.sqlite.driver)
}
