package com.ahuguet.castellsenvena.core.data.storage

/**
 * Small persistent preferences. The app backs it with SharedPreferences; tests
 * use [InMemoryKeyValueStore].
 */
interface KeyValueStore {
    fun getString(key: String): String?
    fun putString(key: String, value: String)
}

class InMemoryKeyValueStore : KeyValueStore {
    private val values = mutableMapOf<String, String>()

    override fun getString(key: String): String? = values[key]

    override fun putString(key: String, value: String) {
        values[key] = value
    }
}
