import org.gradle.api.Plugin
import org.gradle.api.Project

/**
 * Applies SQLDelight from the build-logic classpath. The module declares its
 * database with the `sqldelight { }` block.
 */
class SqlDelightConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        target.pluginManager.apply("app.cash.sqldelight")
    }
}
