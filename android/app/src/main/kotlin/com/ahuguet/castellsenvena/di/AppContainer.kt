package com.ahuguet.castellsenvena.di

import android.content.Context
import android.os.SystemClock
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import com.ahuguet.castellsenvena.BuildConfig
import com.ahuguet.castellsenvena.R
import com.ahuguet.castellsenvena.core.data.chat.DatabaseChatRepository
import com.ahuguet.castellsenvena.core.data.storage.InstallationIdentifierStore
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.network.ApiClient
import com.ahuguet.castellsenvena.core.network.service.HttpChatRemoteService
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorRules
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import com.ahuguet.castellsenvena.navigation.CastellsAppModels
import com.ahuguet.castellsenvena.platform.KeyValueComparatorStorage
import com.ahuguet.castellsenvena.platform.SharedPreferencesKeyValueStore
import com.ahuguet.castellsenvena.startup.StartupGate
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/**
 * The composition root, built once per process: the preferences, the local database, the API
 * client, the calculator, the comparator and the settings.
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    /** Work that must outlive a screen: sends and deletions. */
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    val startupGate = StartupGate(now = SystemClock::uptimeMillis)

    private val keyValueStore = SharedPreferencesKeyValueStore(
        appContext.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE),
    )

    private val configuration = AppConfiguration(
        apiBaseUrl = BuildConfig.API_BASE_URL,
        appName = appContext.getString(R.string.app_name),
        appVersion = BuildConfig.VERSION_NAME,
        buildNumber = BuildConfig.VERSION_CODE.toString(),
        technicalIdentifier = InstallationIdentifierStore(keyValueStore).currentIdentifier(),
    )

    private val apiClient = ApiClient(baseUrl = configuration.apiBaseUrl)

    private val database = CastellsDatabase(
        AndroidSqliteDriver(schema = CastellsDatabase.Schema, context = appContext, name = DATABASE_NAME),
    )

    private val chatRepository = DatabaseChatRepository(
        database = database,
        remoteService = HttpChatRemoteService(apiClient),
        installationId = configuration.technicalIdentifier,
    )

    /** The comparator and its scenarios, or `null` if the bundled score table cannot be read. */
    private val comparator: ComparatorViewModel? = runCatching { ScoreTable.bundled() }.getOrNull()?.let { table ->
        ComparatorViewModel(ComparatorRules(table), KeyValueComparatorStorage(keyValueStore))
    }

    val models = CastellsAppModels(
        conversationList = ConversationListViewModel(chatRepository),
        comparator = comparator,
        chatRepository = chatRepository,
        settingsConfiguration = configuration.settingsConfiguration,
        actionScope = applicationScope,
    )

    private companion object {
        const val PREFERENCES_NAME = "castells"
        const val DATABASE_NAME = "castells.db"
    }
}
