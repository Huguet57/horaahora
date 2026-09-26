import com.android.build.api.dsl.ApplicationExtension
import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

/** Jetpack Compose for an Android application or library module. */
class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply("org.jetbrains.kotlin.plugin.compose")
        pluginManager.withPlugin("com.android.application") {
            extensions.configure<ApplicationExtension> {
                buildFeatures {
                    compose = true
                }
            }
        }
        pluginManager.withPlugin("com.android.library") {
            extensions.configure<LibraryExtension> {
                buildFeatures {
                    compose = true
                }
            }
        }

        dependencies {
            val bom = platform(libs.library("androidx-compose-bom").get())
            add("implementation", bom)
            add("implementation", libs.library("androidx-compose-ui").get())
            add("implementation", libs.library("androidx-compose-foundation").get())
            add("implementation", libs.library("androidx-compose-material3").get())
            add("implementation", libs.library("androidx-compose-ui-tooling-preview").get())
            add("debugImplementation", libs.library("androidx-compose-ui-tooling").get())
        }
    }
}
