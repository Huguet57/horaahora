package com.ahuguet.castellsenvena.core.data.storage

import java.util.UUID

/**
 * The random identifier of this installation. It is the only identifier the
 * backend receives, for rate limiting.
 */
class InstallationIdentifierStore(
    private val store: KeyValueStore,
    private val newIdentifier: () -> String = { UUID.randomUUID().toString().uppercase() },
) {
    fun currentIdentifier(): String =
        store.getString(KEY) ?: newIdentifier().also { store.putString(KEY, it) }

    companion object {
        const val KEY = "castells.installation-id"
    }
}
