package com.ahuguet.castellsenvena.core.network

import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.network.dto.AgendaPageDto
import com.ahuguet.castellsenvena.core.network.dto.CastellerGroupDirectoryDto
import com.ahuguet.castellsenvena.core.network.dto.ChatResponseDto
import com.ahuguet.castellsenvena.core.network.dto.HourByHourPageDto
import com.ahuguet.castellsenvena.core.network.service.ChatResponseCodec
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ContractTest {
    @Test
    fun hourByHourPageDecodesFastApiDatesWithFractionalSeconds() {
        val json = """
            {
              "items": [{
                "id": "item-1",
                "source_id": "revista-castells",
                "external_id": "external-1",
                "title": "Entrada",
                "display_title": "Entrada",
                "summary": "Resum",
                "published_at": "2026-07-20T12:45:22+00:00",
                "source_order": 0,
                "article_url": "https://example.com/article",
                "action_url": null,
                "attribution": "Revista Castells",
                "created_at": "2026-07-20T12:54:09.737320+00:00",
                "updated_at": "2026-07-20T12:54:09.737320"
              }],
              "next_cursor": null,
              "from_cache": false
            }
        """.trimIndent()

        val page = CastellsJson.decodeFromString(HourByHourPageDto.serializer(), json).toDomain()
        val item = page.items.single()

        assertEquals("external-1", item.externalId)
        assertEquals("Entrada", item.displayTitle)
        assertNull(item.actionUrl)
        assertEquals(Instant.parse("2026-07-20T12:45:22Z"), item.publishedAt)
        assertEquals(Instant.parse("2026-07-20T12:54:09.737320Z"), item.createdAt)
        assertEquals(Instant.parse("2026-07-20T12:54:09.737320Z"), item.updatedAt)
    }

    @Test
    fun elMonCastellerArticleDecodesAndOpensItsOriginalUrl() {
        val json = """
            {
              "items": [{
                "id": "item-1",
                "source_id": "el-mon-casteller",
                "external_id": "external-1",
                "title": "Una diada & una estrena",
                "display_title": "Una diada & una estrena",
                "summary": "Una estrena a plaça …",
                "published_at": "2026-09-24T09:08:17Z",
                "source_order": 0,
                "article_url": "https://www.elmoncasteller.cat/una-diada/",
                "action_url": "https://www.elmoncasteller.cat/una-diada/",
                "attribution": "El Món Casteller",
                "created_at": "2026-09-24T10:00:00.123456Z",
                "updated_at": "2026-09-24T10:00:00.123456Z"
              }],
              "next_cursor": null,
              "from_cache": true
            }
        """.trimIndent()

        val page = CastellsJson.decodeFromString(HourByHourPageDto.serializer(), json).toDomain()
        val item = page.items.single()

        assertEquals("el-mon-casteller", item.sourceId)
        assertEquals("Una estrena a plaça …", item.summary)
        assertNotNull(item.publishedAt)
        assertEquals(item.articleUrl, item.associatedUrl)
        assertTrue(page.fromCache)
    }

    @Test
    fun displayTitleFallsBackToTheEditorialTitle() {
        val json = """
            {"items":[{"id":"1","source_id":"s","external_id":"e","title":"Títol","summary":"",
            "published_at":null,"source_order":0,"article_url":"https://example.com","action_url":null,
            "attribution":"A","created_at":"2026-07-20T12:00:00Z","updated_at":"2026-07-20T12:00:00Z"}],
            "next_cursor":"next","from_cache":false}
        """.trimIndent()

        val page = CastellsJson.decodeFromString(HourByHourPageDto.serializer(), json).toDomain()

        assertEquals("Títol", page.items.single().displayTitle)
        assertNull(page.items.single().publishedAt)
        assertEquals("next", page.nextCursor)
    }

    @Test
    fun chatResponseDecodesTheProviderNeutralContract() {
        val json = """
            {
              "reply":"Guanya Vella.",
              "intent":"comparison",
              "performances":[{
                "label":"Vella",
                "total":4930,
                "castells":[{
                  "input":"4d10fm",
                  "canonical":"4de10fm",
                  "outcome":"unloaded",
                  "points":4930,
                  "counted":true,
                  "reason":null
                }]
              }],
              "winner_label":"Vella",
              "warnings":[],
              "ruleset_version":"concurs-2026",
              "needs_clarification":false
            }
        """.trimIndent()

        val response = CastellsJson.decodeFromString(ChatResponseDto.serializer(), json).toDomain()

        assertEquals("Vella", response.winnerLabel)
        assertEquals(4930, response.performances.single().castells.single().points)
        assertNull(response.presentation)
    }

    @Test
    fun chatResponseDecodesStructuredScorePresentation() {
        val json = """
            {
              "reply":"Els dos primers són el 3de10sm i el 4de10sm.",
              "intent":"contest_info",
              "performances":[],
              "winner_label":null,
              "warnings":[],
              "ruleset_version":"concurs-2026",
              "needs_clarification":false,
              "presentation":{
                "type":"score_ranking",
                "title":"Rànquing de puntuacions 2026",
                "outcome":"both",
                "focus_notation":null,
                "rows":[{
                  "position":1,
                  "notation":"3de10sm",
                  "loaded_points":6205,
                  "unloaded_points":7475
                }]
              }
            }
        """.trimIndent()

        val response = CastellsJson.decodeFromString(ChatResponseDto.serializer(), json).toDomain()

        assertEquals("score_ranking", response.presentation?.type)
        assertEquals("both", response.presentation?.outcome)
        assertEquals("3de10sm", response.presentation?.rows?.single()?.notation)
        assertEquals(7_475, response.presentation?.rows?.single()?.unloadedPoints)
    }

    @Test
    fun storedChatResponsesRoundTripThroughTheWireFormat() {
        val json = """
            {"reply":"R","intent":"total","performances":[{"label":"A","total":10,"castells":[
            {"input":"3d8","canonical":"3de8","outcome":"loaded","points":10,"counted":true,"reason":null}]}],
            "winner_label":null,"warnings":["w"],"ruleset_version":"concurs-2026","needs_clarification":false,
            "presentation":null}
        """.trimIndent()
        val response = CastellsJson.decodeFromString(ChatResponseDto.serializer(), json).toDomain()

        val stored = ChatResponseCodec.encode(response)

        assertTrue(stored.contains("\"ruleset_version\":\"concurs-2026\""))
        assertEquals(response, ChatResponseCodec.decodeOrNull(stored))
        assertNull(ChatResponseCodec.decodeOrNull("{not json"))
    }

    @Test
    fun agendaDecodesImpreciseTimeAndNeutralSourceStatus() {
        val json = """
            {
              "items": [{
                "id": "event-1",
                "source_id": "cccc",
                "external_id": "external-1",
                "title": "Diada",
                "local_date": "2026-07-21",
                "starts_at": null,
                "time_label": "Tarda",
                "timezone": "Europe/Madrid",
                "venue": "Plaça",
                "municipality": "Valls",
                "participating_groups": ["Colla A"],
                "notes": "",
                "source_url": "https://castellscat.cat/ca/agenda?a=2026&m=07",
                "source_order": 0,
                "attribution": "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                "revision": "r1",
                "updated_at": "2026-07-21T10:00:00Z"
              }],
              "next_cursor": null,
              "official_url": "https://castellscat.cat/ca/agenda",
              "from_cache": false,
              "source_status": "active"
            }
        """.trimIndent()

        val page = CastellsJson.decodeFromString(AgendaPageDto.serializer(), json).toDomain()

        assertEquals("2026-07-21", page.items.single().localDate)
        assertEquals("Tarda", page.items.single().timeLabel)
        assertNull(page.items.single().startsAt)
        assertEquals(AgendaSourceStatus.ACTIVE, page.sourceStatus)
    }

    @Test
    fun groupDirectoryDecodesTheProviderNeutralContract() {
        val json = """
            {
              "groups": ["Castellers de Vilafranca", "Colla Vella dels Xiquets de Valls"],
              "revision": "2026-07-25",
              "official_url": "https://castellscat.cat/public/ca/les-colles-llistat"
            }
        """.trimIndent()

        val directory = CastellsJson.decodeFromString(CastellerGroupDirectoryDto.serializer(), json).toDomain()

        assertEquals("Castellers de Vilafranca", directory.groups.first())
        assertEquals("2026-07-25", directory.revision)
        assertEquals("https://castellscat.cat/public/ca/les-colles-llistat", directory.officialUrl)
    }
}
