import SwiftData
import SwiftUI
import CastellsData
import CastellsDomain
import FeatureSettings

@main
struct HoraAHoraApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    private let dependencies: AppDependencies

    init() {
        do {
            dependencies = try AppDependencies()
        } catch {
            fatalError("No s'ha pogut preparar la persistència local: \(error.localizedDescription)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView(dependencies: dependencies)
        }
    }
}

@MainActor
final class AppDependencies {
    let modelContainer: ModelContainer
    let hourByHourRepository: any HourByHourRepository
    let agendaRepository: any AgendaRepository
    let chatRepository: any ChatRepository
    let settingsModel: SettingsModel
    let settingsConfiguration: SettingsConfiguration

    init(
        configuration: AppConfiguration = .live(),
        userDefaults: UserDefaults = .standard
    ) throws {
        let modelContainer = try DataStack.makeModelContainer()
        let client = APIClient(baseURL: configuration.apiBaseURL)
        let notificationManager = IOSHourByHourNotificationManager(userDefaults: userDefaults)

        self.modelContainer = modelContainer
        self.hourByHourRepository = CachedHourByHourRepository(
            container: modelContainer,
            remoteService: HTTPHourByHourRemoteService(client: client)
        )
        self.agendaRepository = CachedAgendaRepository(
            container: modelContainer,
            remoteService: HTTPAgendaRemoteService(client: client)
        )
        self.chatRepository = SwiftDataChatRepository(
            container: modelContainer,
            remoteService: HTTPChatRemoteService(client: client),
            installationID: configuration.technicalIdentifier
        )
        self.settingsModel = SettingsModel(
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
        self.settingsConfiguration = configuration.settingsConfiguration
    }
}

struct AppConfiguration {
    static let notificationOnboardingDismissedKey =
        "castells.hour-by-hour.notification-onboarding-dismissed"

    let apiBaseURL: URL
    let supportEmail: String
    let appName: String
    let appVersion: String
    let buildNumber: String
    let technicalIdentifier: String
    let revistaCastellsURL: URL?
    let ccccAgendaURL: URL?
    let concursCastellsURL: URL?

    var settingsConfiguration: SettingsConfiguration {
        SettingsConfiguration(
            apiBaseURL: apiBaseURL,
            supportEmail: supportEmail,
            appName: appName,
            appVersion: appVersion,
            buildNumber: buildNumber,
            technicalIdentifier: technicalIdentifier,
            revistaCastellsURL: revistaCastellsURL,
            ccccAgendaURL: ccccAgendaURL,
            concursCastellsURL: concursCastellsURL
        )
    }

    static func live(
        environment: [String: String] = ProcessInfo.processInfo.environment,
        bundle: Bundle = .main,
        userDefaults: UserDefaults = .standard
    ) -> AppConfiguration {
        let configuredBaseURL = environment["CASTELLS_API_BASE_URL"]
            ?? bundle.object(forInfoDictionaryKey: "CastellsAPIBaseURL") as? String
            ?? "https://castells-superapp-poc.vercel.app"
        guard let apiBaseURL = URL(string: configuredBaseURL) else {
            preconditionFailure("CastellsAPIBaseURL no és una URL vàlida")
        }

        return AppConfiguration(
            apiBaseURL: apiBaseURL,
            supportEmail: "tenimaletaapp@gmail.com",
            appName: "Castells en vena",
            appVersion: bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
                ?? "1.0",
            buildNumber: bundle.object(forInfoDictionaryKey: "CFBundleVersion") as? String
                ?? "1",
            technicalIdentifier: InstallationIdentifierStore(
                userDefaults: userDefaults
            ).currentIdentifier(),
            revistaCastellsURL: URL(
                string: "https://revistacastells.cat/castells-hora-a-hora/"
            ),
            ccccAgendaURL: URL(string: "https://castellscat.cat/public/ca/agenda"),
            // No hi ha encara una URL oficial versionada i estable per a la taula del 2026.
            concursCastellsURL: nil
        )
    }
}

private struct InstallationIdentifierStore {
    private let userDefaults: UserDefaults
    private let key = "castells.installation-id"

    init(userDefaults: UserDefaults) {
        self.userDefaults = userDefaults
    }

    func currentIdentifier() -> String {
        if let existing = userDefaults.string(forKey: key) {
            return existing
        }
        let identifier = UUID().uuidString
        userDefaults.set(identifier, forKey: key)
        return identifier
    }
}
