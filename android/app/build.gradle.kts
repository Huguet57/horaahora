plugins {
    id("castells.android.application")
    id("castells.android.compose")
}

// The API the app talks to. Release builds always use castells.apiBaseUrl (production).
// Debug builds use castells.apiBaseUrl.debug, a local backend, so testing never reaches
// production; CASTELLS_API_BASE_URL overrides it.
val releaseApiBaseUrl: String = providers.gradleProperty("castells.apiBaseUrl").get()

val debugApiBaseUrl: String = providers.environmentVariable("CASTELLS_API_BASE_URL")
    .orElse(providers.gradleProperty("castells.apiBaseUrl.debug"))
    .get()

// The visible version of the iOS and Android apps lives in Version.xcconfig at the repository root.
val marketingVersion: String =
    Regex("""(?m)^MARKETING_VERSION = (\S+)$""")
        .find(rootDir.resolve("../Version.xcconfig").readText())
        ?.groupValues
        ?.get(1)
        ?: error("Version.xcconfig has no MARKETING_VERSION")

// The upload key for Google Play, kept out of the repository. Without it,
// release builds are unsigned.
fun signingValue(name: String): String? =
    providers.gradleProperty("castells.signing.$name").orNull
        ?: providers.environmentVariable("CASTELLS_SIGNING_${name.uppercase()}").orNull
val releaseKeystore: String? = signingValue("storeFile")

android {
    namespace = "com.ahuguet.castellsenvena"

    defaultConfig {
        applicationId = "com.ahuguet.castellsenvena"
        versionCode = providers.gradleProperty("castells.versionCode").orNull?.toInt() ?: 1
        versionName = marketingVersion
    }

    buildFeatures {
        buildConfig = true
    }

    signingConfigs {
        releaseKeystore?.let { keystore ->
            create("release") {
                storeFile = file(keystore)
                storePassword = signingValue("storePassword")
                keyAlias = signingValue("keyAlias")
                keyPassword = signingValue("keyPassword")
            }
        }
    }

    buildTypes {
        debug {
            buildConfigField("String", "API_BASE_URL", "\"$debugApiBaseUrl\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            buildConfigField("String", "API_BASE_URL", "\"$releaseApiBaseUrl\"")
            signingConfig = signingConfigs.findByName("release")
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(projects.core.designsystem)
    implementation(projects.core.data)
    implementation(projects.feature.calculator.ui)
    implementation(projects.feature.scoretable.ui)
    implementation(projects.feature.settings.ui)

    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.browser)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.sqldelight.android.driver)
}
