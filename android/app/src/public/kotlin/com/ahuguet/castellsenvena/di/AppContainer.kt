package com.ahuguet.castellsenvena.di

import android.content.Context
import com.ahuguet.castellsenvena.core.data.notifications.LegacyNewsNotificationsRetirement
import com.ahuguet.castellsenvena.core.network.service.HttpPushSubscriptionRemoteService
import com.ahuguet.castellsenvena.navigation.CastellsAppModels
import com.ahuguet.castellsenvena.platform.AndroidLegacyNewsNotificationsSystem
import com.ahuguet.castellsenvena.startup.StartupGate
import kotlinx.coroutines.launch

/**
 * The composition root of the public app: the calculator, the score table and their
 * settings. It builds nothing of Hora a Hora, Agenda or the news notifications; it only
 * stops the news notifications that an earlier version turned on.
 */
class AppContainer(context: Context) {
    private val core = CoreContainer(context)

    val startupGate: StartupGate get() = core.startupGate

    private val legacyNewsNotifications = LegacyNewsNotificationsRetirement(
        store = core.keyValueStore,
        remoteService = HttpPushSubscriptionRemoteService(
            client = core.apiClient,
            appId = core.configuration.applicationId,
        ),
        installationId = core.configuration.technicalIdentifier,
        environment = core.configuration.pushEnvironment,
        platform = AppConfiguration.PUSH_PLATFORM,
        system = AndroidLegacyNewsNotificationsSystem(context.applicationContext),
    )

    val models = CastellsAppModels(
        conversationList = core.conversationList,
        chatRepository = core.chatRepository,
        settingsConfiguration = core.configuration.settingsConfiguration,
        actionScope = core.applicationScope,
        onForeground = {
            core.applicationScope.launch { legacyNewsNotifications.retireIfNeeded() }
        },
    )
}
