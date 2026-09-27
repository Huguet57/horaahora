package com.ahuguet.castellsenvena.feature.agenda.presentation.calendar

/**
 * Geometry of the monthly calendar that folds into a single week while the
 * event list scrolls. Heights are in dp. Fold progress goes from 0 (the whole
 * month) to 1 (only the active week); releasing at 50% or more snaps folded.
 */
object AgendaCalendarFold {
    const val WEEKDAY_HEADER_HEIGHT = 16f
    const val WEEK_ROW_HEIGHT = 44f
    const val WEEK_ROW_SPACING = 8f

    /** Vertical slot of one week row: the gap above it plus the row. */
    const val WEEK_ROW_SLOT_HEIGHT = WEEK_ROW_SPACING + WEEK_ROW_HEIGHT

    /** Weekday header plus the single remaining (active) week row. */
    const val COLLAPSED_GRID_HEIGHT = WEEKDAY_HEADER_HEIGHT + WEEK_ROW_SLOT_HEIGHT

    /** A month shown in complete Monday-based weeks needs at most six rows. */
    val MAXIMUM_FOLD_DISTANCE: Float = foldDistance(weekRowCount = 6)

    fun expandedGridHeight(weekRowCount: Int): Float =
        WEEKDAY_HEADER_HEIGHT + maxOf(weekRowCount, 1) * WEEK_ROW_SLOT_HEIGHT

    /** The scroll travel that folds the calendar completely. */
    fun foldDistance(weekRowCount: Int): Float = expandedGridHeight(weekRowCount) - COLLAPSED_GRID_HEIGHT

    fun gridHeight(weekRowCount: Int, progress: Float): Float =
        expandedGridHeight(weekRowCount) - foldDistance(weekRowCount) * clamped(progress)

    /** The weeks other than the active one shrink as the calendar folds. */
    fun inactiveWeekRowSlotHeight(progress: Float): Float = WEEK_ROW_SLOT_HEIGHT * (1 - clamped(progress))

    fun progress(scrollOffset: Float, foldDistance: Float): Float =
        if (foldDistance <= 0f) 0f else clamped(scrollOffset / foldDistance)

    /** With reduced motion the calendar never shows intermediate states. */
    fun effectiveProgress(progress: Float, reduceMotion: Boolean): Float = when {
        !reduceMotion -> clamped(progress)
        snapsCollapsed(progress) -> 1f
        else -> 0f
    }

    fun snapsCollapsed(progress: Float): Boolean = progress >= 0.5f

    /** Where a released fold settles, so the calendar never rests half folded. */
    fun restingProgress(progress: Float): Float = if (snapsCollapsed(progress)) 1f else 0f

    /** Adjusts a proposed resting scroll offset out of the fold zone. */
    fun snapTargetOffset(proposedOffset: Float, foldDistance: Float): Float {
        if (proposedOffset <= 0f || proposedOffset >= foldDistance) return proposedOffset
        return if (snapsCollapsed(progress(proposedOffset, foldDistance))) foldDistance else 0f
    }

    private fun clamped(value: Float): Float = value.coerceIn(0f, 1f)
}
