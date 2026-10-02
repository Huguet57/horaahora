package com.ahuguet.castellsenvena.core.data

import app.cash.sqldelight.db.QueryResult
import app.cash.sqldelight.driver.jdbc.sqlite.JdbcSqliteDriver
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.database.ConversationRecord
import java.io.File
import java.util.Properties
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * Databases of earlier versions also hold the offline copies of Hora a Hora and the Agenda.
 * The current schema must open them as they are, without a migration, and keep the
 * conversations.
 */
class LegacyDatabaseTest {
    private val file: File = File.createTempFile("castells", ".db")

    @AfterTest
    fun tearDown() {
        file.delete()
    }

    @Test
    fun theSchemaVersionIsStillTheOneEarlierVersionsCreated() {
        // A higher version would run a migration on every existing database.
        assertEquals(1, CastellsDatabase.Schema.version)
    }

    @Test
    fun databasesWithTheHourByHourAndAgendaTablesOpenWithTheirConversations() {
        JdbcSqliteDriver(url).use { driver ->
            CastellsDatabase.Schema.create(driver)
            LEGACY_TABLES.forEach { driver.execute(null, it, 0) }
            driver.execute(null, "PRAGMA user_version = 1", 0)
            CastellsDatabase(driver).conversationRecordQueries.insert(
                ConversationRecord("conversation", "Concurs", 1, 2),
            )
        }

        // Like AndroidSqliteDriver, it creates or migrates the schema only if user_version asks for it.
        JdbcSqliteDriver(url, Properties(), CastellsDatabase.Schema).use { driver ->
            val conversations = CastellsDatabase(driver).conversationRecordQueries.all().executeAsList()
            assertEquals(listOf("Concurs"), conversations.map { it.title })

            val legacyRows = driver.executeQuery(
                null,
                "SELECT count(*) FROM sqlite_master WHERE name IN ('HourByHourItemRecord', 'AgendaEventRecord')",
                { cursor -> QueryResult.Value(if (cursor.next().value) cursor.getLong(0) else null) },
                0,
            ).value
            assertEquals(2L, legacyRows)
        }
    }

    private val url: String get() = "jdbc:sqlite:${file.absolutePath}"

    private companion object {
        /** The two tables as the last version that had them created them. */
        val LEGACY_TABLES = listOf(
            """
            CREATE TABLE HourByHourItemRecord (
                id TEXT NOT NULL PRIMARY KEY, sourceId TEXT NOT NULL, externalId TEXT NOT NULL,
                title TEXT NOT NULL, displayTitle TEXT, summary TEXT NOT NULL, publishedAt INTEGER,
                sourceOrder INTEGER NOT NULL, articleUrl TEXT NOT NULL, actionUrl TEXT,
                attribution TEXT NOT NULL, createdAt INTEGER NOT NULL, updatedAt INTEGER NOT NULL
            )
            """.trimIndent(),
            """
            CREATE TABLE AgendaEventRecord (
                id TEXT NOT NULL PRIMARY KEY, sourceId TEXT NOT NULL, externalId TEXT NOT NULL,
                title TEXT NOT NULL, localDate TEXT NOT NULL, startsAt INTEGER, timeLabel TEXT NOT NULL,
                timezone TEXT NOT NULL, venue TEXT NOT NULL, municipality TEXT NOT NULL,
                participatingGroups TEXT NOT NULL, notes TEXT NOT NULL, sourceUrl TEXT NOT NULL,
                sourceOrder INTEGER NOT NULL, attribution TEXT NOT NULL, revision TEXT NOT NULL,
                updatedAt INTEGER NOT NULL
            )
            """.trimIndent(),
            "CREATE INDEX AgendaEventRecord_localDate ON AgendaEventRecord(localDate)",
        )
    }
}
