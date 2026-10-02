package com.ahuguet.castellsenvena

import android.app.Application
import com.ahuguet.castellsenvena.di.AppContainer

class CastellsApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}
