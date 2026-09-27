package com.ahuguet.castellsenvena.core.domain.settings

/**
 * Whether the app shows the sections it hides by default: Hora a Hora, Agenda
 * and their settings. A secret gesture in Ajustos shows and hides them.
 */
interface HiddenSectionsPreferences {
    val isUnlocked: Boolean

    fun setUnlocked(unlocked: Boolean)

    /**
     * The first time the notification status is known, users who already receive
     * news notifications keep the sections; everybody else starts without them.
     */
    fun resolveDefault(notificationsEnabled: Boolean)
}
