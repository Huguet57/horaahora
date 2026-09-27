package com.ahuguet.castellsenvena.feature.internalsettings.presentation

import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsCredit

/** Where Hora a Hora and Agenda take their data from, credited while those sections show. */
data class InternalSources(
    val revistaCastellsUrl: String?,
    val elMonCastellerUrl: String?,
    val ccccAgendaUrl: String?,
) {
    val credits: List<SettingsCredit>
        get() = listOf(
            SettingsCredit("Revista Castells", "Font de l'Hora a Hora", revistaCastellsUrl),
            SettingsCredit(
                "El Món Casteller",
                "Notícies, opinió, entrevistes i cròniques de l'Hora a Hora",
                elMonCastellerUrl,
            ),
            SettingsCredit("Coordinadora de Colles Castelleres de Catalunya (CCCC)", "Font de l'Agenda", ccccAgendaUrl),
        )
}

val NotificationInterestLevel.settingsTitle: String
    get() = when (this) {
        NotificationInterestLevel.LOW -> "Totes"
        NotificationInterestLevel.MEDIUM -> "Rellevants"
        NotificationInterestLevel.HIGH -> "Destacades"
    }

val NotificationInterestLevel.settingsDescription: String
    get() = when (this) {
        NotificationInterestLevel.LOW -> "Totes les notícies que publiquem."
        NotificationInterestLevel.MEDIUM -> "Totes les notícies de les teves colles i l’actualitat interessant."
        NotificationInterestLevel.HIGH -> "Notícies excepcionals i novetats interessants de les teves colles."
    }
