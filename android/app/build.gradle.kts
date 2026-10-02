plugins {
    id("castells.android.application")
    id("castells.android.compose")
}

// The build profile. `public` is the app in the stores: the calculator, the score table and
// their settings. `internal` is a separate development app, with its own identifier and
// name, that adds Hora a Hora, Agenda, their settings and the news notifications. It is
// chosen when building, with -Pcastells.buildProfile or CASTELLS_BUILD_PROFILE, and only the
// chosen profile's variants exist. The default is public.
val buildProfile: String = providers.gradleProperty("castells.buildProfile")
    .orElse(providers.environmentVariable("CASTELLS_BUILD_PROFILE"))
    .getOrElse("public")

// The API the app talks to. Release builds always use castells.apiBaseUrl (production).
// Debug builds use castells.apiBaseUrl.debug, a local backend, so testing never reaches
// production; CASTELLS_API_BASE_URL overrides it.
val releaseApiBaseUrl: String = providers.gradleProperty("castells.apiBaseUrl").get()

val debugApiBaseUrl: String = providers.environmentVariable("CASTELLS_API_BASE_URL")
    .orElse(providers.gradleProperty("castells.apiBaseUrl.debug"))
    .get()

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
        versionName = "1.8"
    }

    flavorDimensions += "profile"
    productFlavors {
        create("public") {
            dimension = "profile"
        }
        create("internal") {
            dimension = "profile"
            // An app of its own: it installs next to the public one and can never replace it.
            applicationIdSuffix = ".internal"
            versionNameSuffix = "-internal"
        }
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
            buildConfigField("String", "PUSH_ENVIRONMENT", "\"development\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            buildConfigField("String", "API_BASE_URL", "\"$releaseApiBaseUrl\"")
            buildConfigField("String", "PUSH_ENVIRONMENT", "\"production\"")
            signingConfig = signingConfigs.findByName("release")
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

require(buildProfile in android.productFlavors.names) {
    "CASTELLS_BUILD_PROFILE must be one of ${android.productFlavors.names.joinToString()}, not \"$buildProfile\""
}

androidComponents {
    beforeVariants { variant ->
        variant.enable = variant.flavorName == buildProfile
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

    // Only the internal app: Hora a Hora, Agenda, their settings and the news notifications.
    "internalImplementation"(projects.core.internaldata)
    "internalImplementation"(projects.feature.hourbyhour.ui)
    "internalImplementation"(projects.feature.agenda.ui)
    "internalImplementation"(projects.feature.internalsettings.ui)
    "internalImplementation"(platform(libs.firebase.bom))
    "internalImplementation"(libs.firebase.messaging)
    // Play services bring Fragment 1.1, whose permission results break the
    // Activity Result API used for the notification permission.
    "internalImplementation"(libs.androidx.fragment)
}

// Firebase Cloud Messaging reads the Firebase project from google-services.json, which stays
// out of the repository. Only the internal app uses it, and only if the file lists the
// internal app; otherwise the internal app builds with news notifications unavailable.
val internalApplicationId =
    "${android.defaultConfig.applicationId}${android.productFlavors.getByName("internal").applicationIdSuffix}"
val googleServices = file("google-services.json")
if (buildProfile == "internal" &&
    googleServices.isFile &&
    googleServices.readText().contains("\"$internalApplicationId\"")
) {
    pluginManager.apply("com.google.gms.google-services")
}
