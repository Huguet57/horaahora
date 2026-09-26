package com.ahuguet.castellsenvena.core.data

import app.cash.sqldelight.driver.jdbc.sqlite.JdbcSqliteDriver
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaPage
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import java.io.IOException
import java.time.Instant

/** A fresh SQLite database in memory, with the app's schema. */
fun inMemoryDatabase(): CastellsDatabase {
    val driver = JdbcSqliteDriver(JdbcSqliteDriver.IN_MEMORY)
    CastellsDatabase.Schema.create(driver)
    return CastellsDatabase(driver)
}

fun offline() = IOException("The Internet connection appears to be offline.")

const val OFFICIAL_URL = "https://castellscat.cat/ca/agenda"

fun castellEvent(
    id: String,
    title: String,
    localDate: String = "2026-07-21",
    sourceId: String = "cccc",
    municipality: String = "Valls",
    participatingGroups: List<String> = listOf("Colla A"),
    notes: String = "",
    sourceOrder: Int = 0,
) = CastellEvent(
    id = id,
    sourceId = sourceId,
    externalId = id,
    title = title,
    localDate = localDate,
    startsAt = null,
    timeLabel = "Tarda",
    timezone = "Europe/Madrid",
    venue = "Plaça",
    municipality = municipality,
    participatingGroups = participatingGroups,
    notes = notes,
    sourceUrl = OFFICIAL_URL,
    sourceOrder = sourceOrder,
    attribution = "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
    revision = "r1",
    updatedAt = Instant.parse("2026-07-21T10:00:00Z"),
)

fun agendaPage(
    items: List<CastellEvent>,
    status: AgendaSourceStatus = AgendaSourceStatus.ACTIVE,
    fromCache: Boolean = false,
) = AgendaPage(
    items = items,
    nextCursor = null,
    officialUrl = OFFICIAL_URL,
    fromCache = fromCache,
    sourceStatus = status,
)
