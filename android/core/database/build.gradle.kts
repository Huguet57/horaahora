plugins {
    id("castells.jvm.library")
    id("castells.sqldelight")
}

// Databases created by earlier versions also hold HourByHourItemRecord and AgendaEventRecord,
// the offline copies of Hora a Hora and the Agenda. Nothing reads them anymore, and they stay
// where they are: dropping them would need a migration on every existing database. Keep the
// schema at version 1 unless a migration is really needed, and never reuse those table names.
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
