package com.ahuguet.castellsenvena.core.common

import java.text.Normalizer
import java.util.Locale

/**
 * Text comparisons that ignore case, accents and character width, the
 * equivalent of Foundation's case-, diacritic- and width-insensitive folding.
 */
object TextFolding {
    private val combiningMarks = Regex("\\p{Mn}+")

    /** "Castellers d’Àltafulla" → "castellers d’altafulla". */
    fun fold(value: String): String {
        val decomposed = Normalizer.normalize(value, Normalizer.Form.NFKD)
        return combiningMarks.replace(decomposed, "").lowercase(Locale.ROOT)
    }

    /** Splits [value] on any Unicode whitespace, dropping empty words. */
    fun words(value: String): List<String> {
        val words = mutableListOf<String>()
        val current = StringBuilder()
        for (character in value) {
            if (character.isWhitespace()) {
                if (current.isNotEmpty()) {
                    words += current.toString()
                    current.clear()
                }
            } else {
                current.append(character)
            }
        }
        if (current.isNotEmpty()) words += current.toString()
        return words
    }

    /** Joins the words of [value] with single spaces. */
    fun collapseWhitespace(value: String): String = words(value).joinToString(" ")

    /** Whether [text] contains [query], ignoring case and accents. */
    fun containsIgnoringCaseAndAccents(text: String, query: String): Boolean =
        fold(text).contains(fold(query))
}
