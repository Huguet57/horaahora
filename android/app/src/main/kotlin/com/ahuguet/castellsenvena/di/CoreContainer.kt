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
import com.ahuguet.castellsenvena.core.network.service.HttpPushSubscriptionRemoteService
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorRules
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.ComparatorViewModel
import com.ahuguet.castellsenvena.platform.KeyValueComparatorStorage
import com.ahuguet.castellsenvena.platform.SharedPreferencesKeyValueStore
import com.ahuguet.castellsenvena.startup.StartupGate
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/**
 * What both apps build once per process: the preferences, the local database, the API
 * clients, the calculator and the comparator. Each app's `AppContainer` adds its own
 * sections on top.
 */
class CoreContainer(context: Context) {
    private val appContext = context.applicationContext

    /** Work that must outlive a screen: sends, deletions, subscription writes. */
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    val startupGate = StartupGate(now = SystemClock::uptimeMillis)

    val keyValueStore = SharedPreferencesKeyValueStore(
        appContext.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE),
    )

    val configuration = AppConfiguration(
        apiBaseUrl = BuildConfig.API_BASE_URL,
        pushEnvironment = BuildConfig.PUSH_ENVIRONMENT,
        appName = appContext.getString(R.string.app_name),
        appVersion = BuildConfig.VERSION_NAME,
        buildNumber = BuildConfig.VERSION_CODE.toString(),
        technicalIdentifier = InstallationIdentifierStore(keyValueStore).currentIdentifier(),
        applicationId = BuildConfig.APPLICATION_ID,
    )

    val apiClient = ApiClient(baseUrl = configuration.apiBaseUrl)

    /**
     * Subscriptions to the news notifications, under this app's application ID: the internal
     * app subscribes, and the public app unsubscribes what an earlier version left.
     */
    val pushSubscriptions = HttpPushSubscriptionRemoteService(apiClient, appId = configuration.applicationId)

    /**
     * The whole schema, Hora a Hora and Agenda tables included, in both apps: the public app
     * keeps the database of the versions that had them, and its conversations.
     */
    val database = CastellsDatabase(
        AndroidSqliteDriver(schema = CastellsDatabase.Schema, context = appContext, name = DATABASE_NAME),
    )

    val chatRepository = DatabaseChatRepository(
        database = database,
        remoteService = HttpChatRemoteService(apiClient),
        installationId = configuration.technicalIdentifier,
    )

    val conversationList = ConversationListViewModel(chatRepository)

    /** The comparator and its scenarios, or `null` if the bundled score table cannot be read. */
    val comparator: ComparatorViewModel? = runCatching { ScoreTable.bundled() }.getOrNull()?.let { table ->
        ComparatorViewModel(ComparatorRules(table), KeyValueComparatorStorage(keyValueStore))
    }

    private companion object {
        const val PREFERENCES_NAME = "castells"
        const val DATABASE_NAME = "castells.db"
    }
}
