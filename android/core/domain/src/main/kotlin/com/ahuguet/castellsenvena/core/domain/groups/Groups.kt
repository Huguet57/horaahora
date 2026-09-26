package com.ahuguet.castellsenvena.core.domain.groups

import com.ahuguet.castellsenvena.core.common.TextFolding

data class CastellerGroupDirectory(
    val groups: List<String>,
    val revision: String,
    val officialUrl: String,
)

interface GroupDirectoryRepository {
    suspend fun groupDirectory(forceRefresh: Boolean): CastellerGroupDirectory
}

/**
 * The key that identifies a group regardless of how its name is written. The
 * backend normalizes the keys of notification preferences the same way.
 */
object GroupNameKey {
    fun normalize(name: String): String {
        val apostrophes = name
            .replace('’', '\'')
            .replace('‘', '\'')
            .replace('ʼ', '\'')
        return TextFolding.collapseWhitespace(TextFolding.fold(apostrophes))
    }
}
