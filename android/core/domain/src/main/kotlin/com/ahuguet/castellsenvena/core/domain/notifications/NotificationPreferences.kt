package com.ahuguet.castellsenvena.core.domain.notifications

import com.ahuguet.castellsenvena.core.domain.groups.GroupNameKey

/** The minimum editorial interest of the news the user wants to be notified about. */
enum class NotificationInterestLevel(val wireValue: String) {
    LOW("low"),
    MEDIUM("medium"),
    HIGH("high"),
    ;

    companion object {
        fun fromWireValue(value: String): NotificationInterestLevel? =
            entries.firstOrNull { it.wireValue == value }
    }
}

/** The groups whose news raise the interest of a notification. */
class NotificationGroupSelection(
    val mode: Mode = Mode.ALL,
    keys: List<String> = emptyList(),
) {
    enum class Mode(val wireValue: String) {
        ALL("all"),
        CUSTOM("custom"),
    }

    /** Normalized, deduplicated and sorted; always empty when following every group. */
    val keys: List<String> = if (mode == Mode.ALL) {
        emptyList()
    } else {
        keys.map(GroupNameKey::normalize).filter { it.isNotEmpty() }.distinct().sorted()
    }

    override fun equals(other: Any?): Boolean =
        other is NotificationGroupSelection && other.mode == mode && other.keys == keys

    override fun hashCode(): Int = 31 * mode.hashCode() + keys.hashCode()

    override fun toString(): String = "NotificationGroupSelection(mode=$mode, keys=$keys)"
}
