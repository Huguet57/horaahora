plugins {
    id("castells.jvm.library")
    id("castells.sqldelight")
}

sqldelight {
    databases {
        create("CastellsDatabase") {
            packageName.set("com.ahuguet.castellsenvena.core.database")
        }
    }
}

dependencies {
    // The generated database exposes SQLDelight's runtime types.
    api(libs.sqldelight.runtime)
}
