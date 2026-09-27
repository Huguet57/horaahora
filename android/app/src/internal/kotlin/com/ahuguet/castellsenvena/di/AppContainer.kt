package com.ahuguet.castellsenvena.di

import android.content.Context
import android.os.SystemClock
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.internaldata.agenda.CachedAgendaRepository
import com.ahuguet.castellsenvena.core.internaldata.agenda.KeyValueAgendaFilterStore
import com.ahuguet.castellsenvena.core.internaldata.groups.RemoteGroupDirectoryRepository
import com.ahuguet.castellsenvena.core.internaldata.hourbyhour.CachedHourByHourRepository
import com.ahuguet.castellsenvena.core.internaldata.network.HttpAgendaRemoteService
import com.ahuguet.castellsenvena.core.internaldata.network.HttpGroupDirectoryRemoteService
import com.ahuguet.castellsenvena.core.internaldata.network.HttpHourByHourRemoteService
import com.ahuguet.castellsenvena.core.internaldata.notifications.NotificationPreferenceStore
import com.ahuguet.castellsenvena.core.internaldata.notifications.PushSubscriptionCoordinator
import com.ahuguet.castellsenvena.core.internaldata.settings.KeyValueHiddenSectionsStore
import com.ahuguet.castellsenvena.core.network.service.HttpPushSubscriptionRemoteService
import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaViewModel
import com.ahuguet.castellsenvena.feature.hourbyhour.presentation.HourByHourViewModel
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSettingsModel
import com.ahuguet.castellsenvena.feature.internalsettings.presentation.InternalSources
import com.ahuguet.castellsenvena.navigation.CastellsAppModels
import com.ahuguet.castellsenvena.notifications.AndroidHourByHourNotificationManager
import com.ahuguet.castellsenvena.notifications.FirebasePushTokenProvider
import com.ahuguet.castellsenvena.notifications.NotificationPermissionRequester
import com.ahuguet.castellsenvena.startup.StartupGate
import java.util.Locale
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/**
 * The composition root of the internal app: the calculator and the score table that the
 * public app has, plus Hora a Hora, Agenda, their settings and the news notifications.
 * Like `AppDependencies` on iOS, it builds the app's objects once per process.
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext
    private val core = CoreContainer(appContext)

    /** Work that must outlive a screen: sends, deletions, subscription writes. */
    val applicationScope: CoroutineScope get() = core.applicationScope

    val startupGate: StartupGate get() = core.startupGate

    private val configuration = core.configuration
    private val keyValueStore = core.keyValueStore
    private val agendaFilterStore = KeyValueAgendaFilterStore(keyValueStore)

    val pushSubscriptionCoordinator = PushSubscriptionCoordinator(
        remoteService = HttpPushSubscriptionRemoteService(
            client = core.apiClient,
            appId = configuration.applicationId,
        ),
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

    private val settingsModel = InternalSettingsModel(
        notificationManager = notificationManager,
        notificationOnboardingDismissed = keyValueStore.getBoolean(NOTIFICATION_ONBOARDING_DISMISSED_KEY) ?: false,
        persistNotificationOnboardingDismissal = { dismissed ->
            keyValueStore.putBoolean(NOTIFICATION_ONBOARDING_DISMISSED_KEY, dismissed)
        },
        hiddenSections = KeyValueHiddenSectionsStore(keyValueStore),
        nowMillis = SystemClock::uptimeMillis,
    )

    val models = CastellsAppModels(
        hourByHour = HourByHourViewModel(
            repository = CachedHourByHourRepository(HttpHourByHourRemoteService(core.apiClient), core.database),
        ),
        agenda = AgendaViewModel(
            repository = CachedAgendaRepository(HttpAgendaRemoteService(core.apiClient), core.database),
            groupDirectoryRepository = RemoteGroupDirectoryRepository(HttpGroupDirectoryRemoteService(core.apiClient)),
            filterStore = agendaFilterStore,
        ),
        conversationList = core.conversationList,
        chatRepository = core.chatRepository,
        settings = settingsModel,
        settingsConfiguration = configuration.settingsConfiguration,
        sources = SOURCES,
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
        const val NOTIFICATION_ONBOARDING_DISMISSED_KEY = "castells.hour-by-hour.notification-onboarding-dismissed"

        /** Where Hora a Hora and Agenda take their data from. */
        val SOURCES = InternalSources(
            revistaCastellsUrl = "https://revistacastells.cat/castells-hora-a-hora/",
            elMonCastellerUrl = "https://www.elmoncasteller.cat/",
            ccccAgendaUrl = "https://castellscat.cat/public/ca/agenda",
        )
    }
}
