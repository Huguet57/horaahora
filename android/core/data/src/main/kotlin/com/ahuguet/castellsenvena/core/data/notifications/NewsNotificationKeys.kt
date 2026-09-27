package com.ahuguet.castellsenvena.core.data.notifications

/**
 * Where the news notifications and the hidden sections keep their settings. Earlier versions
 * of the public app wrote them and the internal app still does; the public app looks for them
 * to retire the notifications an earlier version turned on.
 */
object NewsNotificationKeys {
    const val ENABLED = "castells.hour-by-hour.notifications-enabled"
    const val PERMISSION_REQUESTED = "castells.hour-by-hour.notification-permission-requested"
    const val ONBOARDING_DISMISSED = "castells.hour-by-hour.notification-onboarding-dismissed"
    const val MINIMUM_INTEREST = "castells.hour-by-hour.minimum-interest.v1"
    const val SECTIONS_UNLOCKED = "castells.hidden-sections.unlocked"
}
