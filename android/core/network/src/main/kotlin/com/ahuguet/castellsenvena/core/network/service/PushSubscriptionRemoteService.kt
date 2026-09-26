package com.ahuguet.castellsenvena.core.network.service

import com.ahuguet.castellsenvena.core.domain.notifications.NotificationGroupSelection
import com.ahuguet.castellsenvena.core.domain.notifications.NotificationInterestLevel
import com.ahuguet.castellsenvena.core.network.ApiClient
import com.ahuguet.castellsenvena.core.network.dto.GroupSelectionDto
import com.ahuguet.castellsenvena.core.network.dto.PushSubscriptionBodyDto

/** The device registration the backend needs to deliver news notifications. */
data class PushSubscriptionRequest(
    val installationId: String,
    val deviceToken: String,
    val appVersion: String,
    val locale: String,
    val environment: String,
    /** `android` for Firebase Cloud Messaging tokens. */
    val platform: String,
    val minimumInterest: NotificationInterestLevel = NotificationInterestLevel.HIGH,
    val groupSelection: NotificationGroupSelection = NotificationGroupSelection(),
)

interface PushSubscriptionRemoteService {
    suspend fun register(request: PushSubscriptionRequest)
    suspend fun unregister(installationId: String, environment: String, platform: String)
}

class HttpPushSubscriptionRemoteService(private val client: ApiClient) : PushSubscriptionRemoteService {
    override suspend fun register(request: PushSubscriptionRequest) {
        client.put(
            path = "/v1/push-subscriptions/${request.installationId}",
            body = PushSubscriptionBodyDto(
                deviceToken = request.deviceToken,
                appVersion = request.appVersion,
                locale = request.locale,
                environment = request.environment,
                minimumInterest = request.minimumInterest.wireValue,
                groupSelection = GroupSelectionDto(
                    mode = request.groupSelection.mode.wireValue,
                    keys = request.groupSelection.keys,
                ),
                platform = request.platform,
            ),
            serializer = PushSubscriptionBodyDto.serializer(),
        )
    }

    override suspend fun unregister(installationId: String, environment: String, platform: String) {
        client.delete(
            path = "/v1/push-subscriptions/$installationId",
            query = listOf("environment" to environment, "platform" to platform),
        )
    }
}
