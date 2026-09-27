import Foundation
import CastellsData

/// The composition root of the public app: the calculator, the score table and their settings.
/// It builds nothing of Hora a Hora, Agenda or the news notifications; it only stops the news
/// notifications that an earlier version turned on.
@MainActor
final class PublicAppDependencies {
    let core: CoreDependencies
    let legacyNewsNotifications: LegacyNewsNotificationsRetirement

    init(
        configuration: AppConfiguration = .live(),
        userDefaults: UserDefaults = .standard
    ) throws {
        core = try CoreDependencies(configuration: configuration, userDefaults: userDefaults)
        legacyNewsNotifications = LegacyNewsNotificationsRetirement(
            userDefaults: userDefaults,
            remoteService: HTTPPushSubscriptionRemoteService(
                client: core.apiClient,
                appID: configuration.bundleIdentifier
            ),
            installationID: configuration.technicalIdentifier,
            environment: configuration.apnsEnvironment,
            system: IOSLegacyNewsNotificationsSystem()
        )
    }
}
