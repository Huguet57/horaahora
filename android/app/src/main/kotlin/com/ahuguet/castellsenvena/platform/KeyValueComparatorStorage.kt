package com.ahuguet.castellsenvena.platform

import com.ahuguet.castellsenvena.core.data.storage.KeyValueStore
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorStorage
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel

/** The comparator's scenarios, kept only on the device with the rest of the preferences. */
class KeyValueComparatorStorage(private val store: KeyValueStore) : ComparatorStorage {
    override fun load(): String? = store.getString(ComparatorViewModel.STORAGE_KEY)

    override fun save(value: String) {
        store.putString(ComparatorViewModel.STORAGE_KEY, value)
    }
}
