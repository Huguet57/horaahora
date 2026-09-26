package com.ahuguet.castellsenvena.platform

import android.content.SharedPreferences
import androidx.core.content.edit
import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore

/** The app preferences, the Android counterpart of `UserDefaults`. */
class SharedPreferencesKeyValueStore(private val preferences: SharedPreferences) : KeyValueStore {
    override fun getString(key: String): String? = preferences.getString(key, null)

    override fun putString(key: String, value: String) {
        preferences.edit { putString(key, value) }
    }

    override fun getBoolean(key: String): Boolean? =
        if (preferences.contains(key)) preferences.getBoolean(key, false) else null

    override fun putBoolean(key: String, value: Boolean) {
        preferences.edit { putBoolean(key, value) }
    }

    override fun remove(key: String) {
        preferences.edit { remove(key) }
    }
}
