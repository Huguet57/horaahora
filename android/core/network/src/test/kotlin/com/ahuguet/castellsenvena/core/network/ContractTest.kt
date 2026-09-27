package com.ahuguet.castellsenvena.core.network

import com.ahuguet.castellsenvena.core.network.dto.ChatResponseDto
import com.ahuguet.castellsenvena.core.network.service.ChatResponseCodec
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ContractTest {
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
}
