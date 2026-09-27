package com.ahuguet.castellsenvena.feature.settings.presentation

import java.net.URLDecoder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class SettingsConfigurationTest {
    @Test
    fun privacyUrlIsBuiltBelowTheInjectedApiBaseUrl() {
        assertEquals(
            "https://example.test/service/privacy",
            configuration(apiBaseUrl = "https://example.test/service/").privacyUrl,
        )
        assertEquals("https://example.test/privacy", configuration(apiBaseUrl = "https://example.test").privacyUrl)
    }

    @Test
    fun supportEmailUrlIncludesEditableEncodedMetadata() {
        val url = configuration(
            supportEmail = "suport+castells@example.test",
            appVersion = "2.4",
            buildNumber = "91",
            technicalIdentifier = "ABC 123/ç",
        ).supportEmailUrl

        assertTrue(url.startsWith("mailto:suport+castells@example.test?"))
        val query = url.substringAfter('?').split('&').associate { parameter ->
            parameter.substringBefore('=') to URLDecoder.decode(parameter.substringAfter('='), Charsets.UTF_8)
        }
        assertEquals("Suport La calculadora de l'Aleta", query["subject"])
        assertTrue(query.getValue("body").contains("Versió: 2.4 (91)"))
        assertTrue(query.getValue("body").contains("Identificador tècnic: ABC 123/ç"))
        assertTrue(url.contains("%0A"))
        assertTrue(url.contains("%C3%A7"))
        assertFalse(url.contains(' '))
        assertEquals("Versió 2.4 (91)", configuration(appVersion = "2.4", buildNumber = "91").versionAndBuild)
    }

    @Test
    fun theCalculatorCreditsOnlyTheOfficialScoreTable() {
        assertEquals(
            listOf(
                SettingsCredit(
                    name = "Taula oficial del Concurs de Castells 2026",
                    detail = "Font de la calculadora i de les puntuacions",
                    url = null,
                ),
            ),
            configuration().credits,
        )
    }

    private fun configuration(
        apiBaseUrl: String = "https://example.test",
        supportEmail: String = "support@example.test",
        appVersion: String = "1.0",
        buildNumber: String = "1",
        technicalIdentifier: String = "test-id",
    ) = SettingsConfiguration(
        apiBaseUrl = apiBaseUrl,
        supportEmail = supportEmail,
        appName = "La calculadora de l'Aleta",
        appVersion = appVersion,
        buildNumber = buildNumber,
        technicalIdentifier = technicalIdentifier,
        concursCastellsUrl = null,
    )
}
