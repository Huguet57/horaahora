package com.ahuguet.castellsenvena.feature.hourbyhour.presentation

import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import java.time.LocalDate
import java.time.ZoneId

/** The items published on one day, in the device's time zone. */
data class HourByHourDayGroup(
    /** Stable across reloads, so list sections keep their identity. */
    val id: String,
    /** Null for items without a publication date. */
    val day: LocalDate?,
    val items: List<HourByHourItem>,
)

internal object HourByHourDayGrouping {
    fun groups(items: List<HourByHourItem>, zone: ZoneId): List<HourByHourDayGroup> {
        val orderedDays = mutableListOf<LocalDate?>()
        val itemsByDay = mutableMapOf<LocalDate?, MutableList<HourByHourItem>>()
        for (item in items) {
            val day = item.publishedAt?.atZone(zone)?.toLocalDate()
            itemsByDay.getOrPut(day) {
                orderedDays += day
                mutableListOf()
            } += item
        }
        return orderedDays.map { day ->
            HourByHourDayGroup(
                id = day?.let { "day-$it" } ?: "undated",
                day = day,
                items = itemsByDay.getValue(day),
            )
        }
    }
}
