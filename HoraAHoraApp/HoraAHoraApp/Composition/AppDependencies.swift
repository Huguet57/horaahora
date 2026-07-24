import Foundation
import SwiftData
import CastellsData
import CastellsDomain
import FeatureSettings

@MainActor
final class AppDependencies {
    let modelContainer: ModelContainer
    let hourByHourRepository: any HourByHourRepository
    let agendaRepository: any AgendaRepository
    let chatRepository: any ChatRepository
    let settingsModel: SettingsModel
    let settingsConfiguration: SettingsConfiguration
    let pushSubscriptionCoordinator: PushSubscriptionCoordinator

    init(
        configuration: AppConfiguration = .live(),
        userDefaults: UserDefaults = .standard
    ) throws {
        let modelContainer = try DataStack.makeModelContainer()
        let client = APIClient(baseURL: configuration.apiBaseURL)
        let pushSubscriptionCoordinator = PushSubscriptionCoordinator(
            remoteService: HTTPPushSubscriptionRemoteService(client: client),
            installationID: configuration.technicalIdentifier,
            appVersion: "\(configuration.appVersion) (\(configuration.buildNumber))",
            locale: Locale.current.identifier,
            environment: configuration.apnsEnvironment
        )
        let notificationManager = IOSHourByHourNotificationManager(
            userDefaults: userDefaults,
            pushSubscriptionCoordinator: pushSubscriptionCoordinator
        )

        self.modelContainer = modelContainer
        hourByHourRepository = CachedHourByHourRepository(
            container: modelContainer,
            remoteService: HTTPHourByHourRemoteService(client: client)
        )
        agendaRepository = CachedAgendaRepository(
            container: modelContainer,
            remoteService: HTTPAgendaRemoteService(client: client)
        )
        chatRepository = SwiftDataChatRepository(
            container: modelContainer,
            remoteService: HTTPChatRemoteService(client: client),
            installationID: configuration.technicalIdentifier
        )
        settingsModel = SettingsModel(
            notificationManager: notificationManager,
            notificationOnboardingDismissed: userDefaults.bool(
                forKey: AppConfiguration.notificationOnboardingDismissedKey
            ),
            persistNotificationOnboardingDismissal: { dismissed in
                userDefaults.set(
                    dismissed,
                    forKey: AppConfiguration.notificationOnboardingDismissedKey
                )
            }
        )
        settingsConfiguration = configuration.settingsConfiguration
        self.pushSubscriptionCoordinator = pushSubscriptionCoordinator
    }
}
