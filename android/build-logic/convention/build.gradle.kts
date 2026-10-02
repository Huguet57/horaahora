import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    `kotlin-dsl`
}

group = "com.ahuguet.castellsenvena.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_17
    }
}

// Without the Android toolchain only the JVM conventions are built; see the
// root settings.gradle.kts.
val jvmOnly = providers.gradleProperty("castells.jvmOnly").orNull == "true"

if (!jvmOnly) {
    kotlin.sourceSets.named("main") {
        kotlin.srcDir("src/android/kotlin")
    }
}

// The conventions compile against the plugins' public APIs. The plugins
// themselves are runtime dependencies, so every module loads them from this
// single classpath.
dependencies {
    compileOnly(libs.kotlin.gradleApi)
    runtimeOnly(libs.kotlin.gradlePlugin)
    runtimeOnly(libs.kotlin.serialization.gradlePlugin)
    runtimeOnly(libs.sqldelight.gradlePlugin)
    if (!jvmOnly) {
        compileOnly(libs.android.gradleApi)
        runtimeOnly(libs.android.gradlePlugin)
        runtimeOnly(libs.compose.compiler.gradlePlugin)
    }
}

// Gradle compiles build logic with its embedded Kotlin, which cannot read the
// metadata of the newer standard library that the plugin APIs depend on.
configurations.named("compileClasspath") {
    resolutionStrategy.force("org.jetbrains.kotlin:kotlin-stdlib:$embeddedKotlinVersion")
}

gradlePlugin {
    plugins {
        register("jvmLibrary") {
            id = "castells.jvm.library"
            implementationClass = "JvmLibraryConventionPlugin"
        }
        register("kotlinSerialization") {
            id = "castells.kotlin.serialization"
            implementationClass = "KotlinSerializationConventionPlugin"
        }
        register("sqldelight") {
            id = "castells.sqldelight"
            implementationClass = "SqlDelightConventionPlugin"
        }
        if (!jvmOnly) {
            register("androidApplication") {
                id = "castells.android.application"
                implementationClass = "AndroidApplicationConventionPlugin"
            }
            register("androidLibrary") {
                id = "castells.android.library"
                implementationClass = "AndroidLibraryConventionPlugin"
            }
            register("androidCompose") {
                id = "castells.android.compose"
                implementationClass = "AndroidComposeConventionPlugin"
            }
            register("androidFeature") {
                id = "castells.android.feature"
                implementationClass = "AndroidFeatureConventionPlugin"
            }
        }
    }
}
