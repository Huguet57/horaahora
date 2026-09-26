package com.ahuguet.castellsenvena.core.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal data class PushSubscriptionBodyDto(
    @SerialName("device_token") val deviceToken: String,
    @SerialName("app_version") val appVersion: String,
    val locale: String,
    val environment: String,
    @SerialName("minimum_interest") val minimumInterest: String,
    @SerialName("group_selection") val groupSelection: GroupSelectionDto,
    val platform: String,
)

@Serializable
internal data class GroupSelectionDto(
    val mode: String,
    val keys: List<String>,
)
