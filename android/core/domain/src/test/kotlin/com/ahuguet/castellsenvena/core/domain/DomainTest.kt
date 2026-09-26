package com.ahuguet.castellsenvena.core.domain

import com.ahuguet.castellsenvena.core.domain.groups.GroupNameKey
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class DomainTest {
    @Test
    fun revistaCastellsOnlyExposesADedicatedAssociatedLink() {
        val now = Instant.now()
        val linked = item(sourceId = "revista-castells", actionUrl = "https://example.com/action", now = now)
        val legacyFallback = item(sourceId = "revista-castells", actionUrl = ARTICLE_URL, now = now)

        assertEquals("https://example.com/action", linked.associatedUrl)
        assertNull(legacyFallback.associatedUrl)
    }

    @Test
    fun otherSourcesOpenTheirOriginalArticle() {
        val article = item(sourceId = "el-mon-casteller", actionUrl = ARTICLE_URL, now = Instant.now())

        assertEquals(ARTICLE_URL, article.associatedUrl)
    }

    @Test
    fun groupKeysIgnoreCaseAccentsWhitespaceAndApostropheVariants() {
        assertEquals(
            GroupNameKey.normalize("castellers d'altafulla"),
            GroupNameKey.normalize("  Castellers   d’Àltafulla "),
        )
        assertEquals("castellers de la vila de gracia", GroupNameKey.normalize("Castellers de la Vila de Gràcia"))
    }

    @Test
    fun groupSelectionNormalizesAndSerializesStableKeys() {
        val selection = NotificationGroupSelection(NotificationGroupSelection.Mode.CUSTOM, listOf(" Minyons ", "MINYONS"))
        assertEquals(listOf("minyons"), selection.keys)

        val all = NotificationGroupSelection(NotificationGroupSelection.Mode.ALL, listOf("Minyons"))
        assertEquals(emptyList(), all.keys)
        assertEquals(NotificationGroupSelection(), all)
    }

    private fun item(sourceId: String, actionUrl: String?, now: Instant) = HourByHourItem(
        id = "id",
        sourceId = sourceId,
        externalId = "external",
        title = "Títol",
        displayTitle = "Títol",
        summary = "",
        publishedAt = now,
        sourceOrder = 0,
        articleUrl = ARTICLE_URL,
        actionUrl = actionUrl,
        attribution = "Font",
        createdAt = now,
        updatedAt = now,
    )

    private companion object {
        const val ARTICLE_URL = "https://example.com/article"
    }
}
