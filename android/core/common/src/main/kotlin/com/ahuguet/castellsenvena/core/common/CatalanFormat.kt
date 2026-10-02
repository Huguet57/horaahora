package com.ahuguet.castellsenvena.core.common

object CatalanNumbers {
    /** Groups thousands with a dot, as Catalan does: 4930 → "4.930". */
    fun grouped(value: Long): String {
        val digits = if (value < 0) (-value).toString() else value.toString()
        val grouped = digits.reversed().chunked(3).joinToString(".").reversed()
        return if (value < 0) "-$grouped" else grouped
    }

    fun grouped(value: Int): String = grouped(value.toLong())
}
