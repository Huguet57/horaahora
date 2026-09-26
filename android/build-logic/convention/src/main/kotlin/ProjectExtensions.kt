import org.gradle.api.Project
import org.gradle.api.artifacts.MinimalExternalModuleDependency
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.testing.Test
import org.gradle.api.tasks.testing.logging.TestExceptionFormat
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmExtension

internal val Project.libs: VersionCatalog
    get() = extensions.getByType<VersionCatalogsExtension>().named("libs")

internal fun VersionCatalog.library(alias: String): Provider<MinimalExternalModuleDependency> =
    findLibrary(alias).orElseThrow { IllegalArgumentException("Unknown library alias $alias") }

internal fun VersionCatalog.intVersion(alias: String): Int =
    findVersion(alias).orElseThrow { IllegalArgumentException("Unknown version $alias") }
        .requiredVersion
        .toInt()

/**
 * Kotlin module names must be unique inside the APK, and several modules share
 * the same directory name (`presentation`, `ui`).
 */
internal val Project.kotlinModuleName: String
    get() = "castells" + path.replace(':', '-')

/** Shared by JVM and Android modules: both expose a [KotlinJvmExtension]. */
internal fun Project.configureKotlinJvmCompilation() {
    val kotlin = extensions.getByName("kotlin") as KotlinJvmExtension
    kotlin.compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
    kotlin.compilerOptions.moduleName.set(kotlinModuleName)
}

internal fun Project.addUnitTestDependencies(configuration: String = "testImplementation") {
    dependencies.add(configuration, libs.library("kotlin-test-junit"))
    dependencies.add(configuration, libs.library("junit4"))
    dependencies.add(configuration, libs.library("kotlinx-coroutines-test"))
}

internal fun Project.configureTestLogging() {
    tasks.withType<Test>().configureEach {
        testLogging {
            events("failed")
            exceptionFormat = TestExceptionFormat.FULL
        }
    }
}
