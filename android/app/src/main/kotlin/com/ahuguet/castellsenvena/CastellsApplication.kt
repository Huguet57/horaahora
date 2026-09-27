package com.ahuguet.castellsenvena

import android.app.Application
import com.ahuguet.castellsenvena.di.AppContainer
import com.ahuguet.castellsenvena.notifications.HourByHourNotifications

class CastellsApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }

    override fun onCreate() {
        super.onCreate()
        HourByHourNotifications.createChannel(this)
    }
}
