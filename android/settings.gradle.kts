pluginManagement {
    includeBuild("build-logic")
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android(\\..*)?")
                includeGroupByRegex("com\\.google\\.(android|testing)(\\..*)?")
                includeGroupByRegex("androidx(\\..*)?")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android(\\..*)?")
                includeGroupByRegex("com\\.google\\.(android|testing)(\\..*)?")
                includeGroupByRegex("androidx(\\..*)?")
            }
        }
        mavenCentral()
    }
}

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

rootProject.name = "castells-en-vena"

// Platform-independent modules: domain, data and presentation logic. They build
// and run their tests on any JVM, without the Android SDK.
include(
    ":core:common",
    ":core:domain",
    ":core:network",
    ":core:database",
    ":core:data",
    ":feature:calculator:presentation",
    ":feature:scoretable:presentation",
    ":feature:settings:presentation",
)

// Android modules need the Android SDK and Google's Maven repository. Pass
// -Pcastells.jvmOnly=true to work on the modules above without them.
if (providers.gradleProperty("castells.jvmOnly").orNull != "true") {
    include(
        ":app",
        ":core:designsystem",
        ":feature:calculator:ui",
        ":feature:scoretable:ui",
        ":feature:settings:ui",
    )
}
