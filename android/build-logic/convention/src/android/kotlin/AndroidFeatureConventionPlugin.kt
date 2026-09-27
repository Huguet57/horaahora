import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies

/**
 * The Android UI of a feature: Compose screens on top of the feature's
 * platform-independent presentation module and the shared design system.
 */
class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply(AndroidLibraryConventionPlugin::class.java)
        pluginManager.apply(AndroidComposeConventionPlugin::class.java)

        dependencies {
            add("implementation", project(":core:common"))
            add("implementation", project(":core:domain"))
            add("implementation", project(":core:designsystem"))
            add("implementation", libs.library("androidx-activity-compose").get())
            add("implementation", libs.library("androidx-lifecycle-runtime-compose").get())
            add("implementation", libs.library("androidx-compose-material-icons-extended").get())
            add("implementation", libs.library("kotlinx-coroutines-core").get())
        }
    }
}
