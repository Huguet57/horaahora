import Foundation
import CastellsData
import CastellsDomain
import CastellsInternalData
import FeatureAgenda
import FeatureInternalSettings

/// The composition root of the internal app: the calculator and the score table of the public
/// app, plus Hora a Hora, Agenda, their settings and the news notifications.
@MainActor
final class InternalAppDependencies {
    static let notificationOnboardingDismissedKey = NewsNotificationKeys.onboardingDismissed
    /// Where Hora a Hora and Agenda take their data from.
    static let sources = InternalSources(
        revistaCastellsURL: URL(string: "https://revistacastells.cat/castells-hora-a-hora/"),
        elMonCastellerURL: URL(string: "https://www.elmoncasteller.cat/"),
        ccccAgendaURL: URL(string: "https://castellscat.cat/public/ca/agenda")
    )

    let core: CoreDependencies
    let hourByHourRepository: any HourByHourRepository
    let agendaRepository: any AgendaRepository
    let groupDirectoryRepository: any GroupDirectoryRepository
    let agendaFilterStore: any AgendaFilterStoring
    let internalSettingsModel: InternalSettingsModel
    let pushSubscriptionCoordinator: PushSubscriptionCoordinator

    init(
        configuration: AppConfiguration = .live(),
        userDefaults: UserDefaults = .standard
    ) throws {
        let core = try CoreDependencies(configuration: configuration, userDefaults: userDefaults)
        let client = core.apiClient
        let agendaFilterStore = AgendaUserDefaultsStore(userDefaults: userDefaults)
        let notificationPreferenceStore = NotificationPreferenceStore(userDefaults: userDefaults)
        let hiddenSections = HiddenSectionsStore(userDefaults: userDefaults)
        let pushSubscriptionCoordinator = PushSubscriptionCoordinator(
            remoteService: core.pushSubscriptions,
            installationID: configuration.technicalIdentifier,
            appVersion: "\(configuration.appVersion) (\(configuration.buildNumber))",
            locale: Locale.current.identifier,
            environment: configuration.apnsEnvironment
        )
        let notificationManager = IOSHourByHourNotificationManager(
            userDefaults: userDefaults,
            pushSubscriptionCoordinator: pushSubscriptionCoordinator,
            preferenceStore: notificationPreferenceStore,
            groupSelection: { [weak agendaFilterStore] in
                switch agendaFilterStore?.load().selection ?? .all {
                case .all: return NotificationGroupSelection()
                case let .custom(keys):
                    return NotificationGroupSelection(mode: .custom, keys: Array(keys))
                }
            }
        )
        agendaFilterStore.onSelectionChange = { [weak notificationManager] _ in
            Task { await notificationManager?.synchronizePreferences() }
        }

        self.core = core
        hourByHourRepository = CachedHourByHourRepository(
            container: core.modelContainer,
            remoteService: HTTPHourByHourRemoteService(client: client)
        )
        agendaRepository = CachedAgendaRepository(
            container: core.modelContainer,
            remoteService: HTTPAgendaRemoteService(client: client)
        )
        groupDirectoryRepository = RemoteGroupDirectoryRepository(
            remoteService: HTTPGroupDirectoryRemoteService(client: client)
        )
        self.agendaFilterStore = agendaFilterStore
        internalSettingsModel = InternalSettingsModel(
            notificationManager: notificationManager,
            notificationOnboardingDismissed: userDefaults.bool(
                forKey: Self.notificationOnboardingDismissedKey
            ),
            persistNotificationOnboardingDismissal: { dismissed in
                userDefaults.set(dismissed, forKey: Self.notificationOnboardingDismissedKey)
            },
            hiddenSections: hiddenSections
        )
        self.pushSubscriptionCoordinator = pushSubscriptionCoordinator
        Task { [internalSettingsModel] in
            await pushSubscriptionCoordinator.observeSynchronization { [weak internalSettingsModel] pending in
                internalSettingsModel?.setNotificationSynchronizationPending(pending)
            }
        }
    }
}
