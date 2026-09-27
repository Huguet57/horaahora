package com.ahuguet.castellsenvena.di

import android.content.Context
import android.os.SystemClock
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import com.ahuguet.castellsenvena.BuildConfig
import com.ahuguet.castellsenvena.core.data.agenda.CachedAgendaRepository
import com.ahuguet.castellsenvena.core.data.agenda.KeyValueAgendaFilterStore
import com.ahuguet.castellsenvena.core.data.chat.DatabaseChatRepository
import com.ahuguet.castellsenvena.core.data.groups.RemoteGroupDirectoryRepository
import com.ahuguet.castellsenvena.core.data.hourbyhour.CachedHourByHourRepository
import com.ahuguet.castellsenvena.core.data.notifications.NotificationPreferenceStore
import com.ahuguet.castellsenvena.core.data.notifications.PushSubscriptionCoordinator
import com.ahuguet.castellsenvena.core.data.storage.InstallationIdentifierStore
import com.ahuguet.castellsenvena.core.database.CastellsDatabase
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.network.ApiClient
import com.ahuguet.castellsenvena.core.network.service.HttpAgendaRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpChatRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpGroupDirectoryRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpHourByHourRemoteService
import com.ahuguet.castellsenvena.core.network.service.HttpPushSubscriptionRemoteService
import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaViewModel
import com.ahuguet.castellsenvena.feature.calculator.presentation.ConversationListViewModel
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourViewModel
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsModel
import com.ahuguet.castellsenvena.navigation.CastellsAppModels
import com.ahuguet.castellsenvena.notifications.AndroidHourByHourNotificationManager
import com.ahuguet.castellsenvena.notifications.FirebasePushTokenProvider
import com.ahuguet.castellsenvena.notifications.NotificationPermissionRequester
import com.ahuguet.castellsenvena.platform.SharedPreferencesKeyValueStore
import com.ahuguet.castellsenvena.startup.StartupGate
import java.util.Locale
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * The composition root: builds the app's objects once per process and wires
 * them together, like `AppDependencies` on iOS.
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    /** Work that must outlive a screen: sends, deletions, subscription writes. */
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    val startupGate = StartupGate(now = SystemClock::uptimeMillis)

    private val keyValueStore = SharedPreferencesKeyValueStore(
        appContext.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE),
    )

    val configuration = AppConfiguration(
        apiBaseUrl = BuildConfig.API_BASE_URL,
        pushEnvironment = BuildConfig.PUSH_ENVIRONMENT,
        appVersion = BuildConfig.VERSION_NAME,
        buildNumber = BuildConfig.VERSION_CODE.toString(),
        technicalIdentifier = InstallationIdentifierStore(keyValueStore).currentIdentifier(),
    )

    private val apiClient = ApiClient(baseUrl = configuration.apiBaseUrl)
    private val database = CastellsDatabase(
        AndroidSqliteDriver(schema = CastellsDatabase.Schema, context = appContext, name = DATABASE_NAME),
    )

    private val agendaFilterStore = KeyValueAgendaFilterStore(keyValueStore)
    private val chatRepository = DatabaseChatRepository(
        database = database,
        remoteService = HttpChatRemoteService(apiClient),
        installationId = configuration.technicalIdentifier,
    )

    val pushSubscriptionCoordinator = PushSubscriptionCoordinator(
        remoteService = HttpPushSubscriptionRemoteService(apiClient),
        installationId = configuration.technicalIdentifier,
        appVersion = "${configuration.appVersion} (${configuration.buildNumber})",
        locale = Locale.getDefault().toLanguageTag(),
        environment = configuration.pushEnvironment,
        platform = AppConfiguration.PUSH_PLATFORM,
    )

    val notificationPermissionRequester = NotificationPermissionRequester()

    private val notificationManager = AndroidHourByHourNotificationManager(
        context = appContext,
        store = keyValueStore,
        pushSubscriptionCoordinator = pushSubscriptionCoordinator,
        preferenceStore = NotificationPreferenceStore(keyValueStore),
        permissionRequester = notificationPermissionRequester,
        tokenProvider = FirebasePushTokenProvider(appContext),
        // Notifications follow the groups chosen in the Agenda.
        groupSelection = {
            when (val selection = agendaFilterStore.load().selection) {
                AgendaGroupSelection.All -> NotificationGroupSelection()
                is AgendaGroupSelection.Custom ->
                    NotificationGroupSelection(NotificationGroupSelection.Mode.CUSTOM, selection.keys.toList())
            }
        },
    )

    private val settingsModel = SettingsModel(
        notificationManager = notificationManager,
        notificationOnboardingDismissed = keyValueStore.getBoolean(NOTIFICATION_ONBOARDING_DISMISSED_KEY) ?: false,
        persistNotificationOnboardingDismissal = { dismissed ->
            keyValueStore.putBoolean(NOTIFICATION_ONBOARDING_DISMISSED_KEY, dismissed)
        },
    )

    val models = CastellsAppModels(
        hourByHour = HourByHourViewModel(
            repository = CachedHourByHourRepository(HttpHourByHourRemoteService(apiClient), database),
        ),
        agenda = AgendaViewModel(
            repository = CachedAgendaRepository(HttpAgendaRemoteService(apiClient), database),
            groupDirectoryRepository = RemoteGroupDirectoryRepository(HttpGroupDirectoryRemoteService(apiClient)),
            filterStore = agendaFilterStore,
        ),
        conversationList = ConversationListViewModel(chatRepository),
        chatRepository = chatRepository,
        settings = settingsModel,
        settingsConfiguration = configuration.settingsConfiguration,
        actionScope = applicationScope,
    )

    init {
        agendaFilterStore.onSelectionChange = {
            applicationScope.launch { notificationManager.synchronizePreferences() }
        }
        applicationScope.launch {
            pushSubscriptionCoordinator.synchronizationPending.collect { pending ->
                settingsModel.setNotificationSynchronizationPending(pending)
            }
        }
    }

    private companion object {
        const val PREFERENCES_NAME = "castells"
        const val DATABASE_NAME = "castells.db"
        const val NOTIFICATION_ONBOARDING_DISMISSED_KEY = "castells.hour-by-hour.notification-onboarding-dismissed"
    }
}
