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
}
