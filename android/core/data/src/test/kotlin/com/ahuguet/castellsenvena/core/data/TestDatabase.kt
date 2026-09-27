package com.ahuguet.castellsenvena.core.data

import app.cash.sqldelight.driver.jdbc.sqlite.JdbcSqliteDriver
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import java.io.IOException

/** A fresh SQLite database in memory, with the app's schema. */
fun inMemoryDatabase(): CastellsDatabase {
    val driver = JdbcSqliteDriver(JdbcSqliteDriver.IN_MEMORY)
    CastellsDatabase.Schema.create(driver)
    return CastellsDatabase(driver)
}

fun offline() = IOException("The Internet connection appears to be offline.")
