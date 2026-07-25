import Foundation
import FeatureSettings

struct AppConfiguration {
    static let notificationOnboardingDismissedKey =
        "castells.hour-by-hour.notification-onboarding-dismissed"

    let apiBaseURL: URL
    let supportEmail: String
    let appName: String
    let appVersion: String
    let buildNumber: String
    let technicalIdentifier: String
    let apnsEnvironment: String
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
        #if DEBUG
        let apnsEnvironment = "development"
        #else
        let apnsEnvironment = "production"
        #endif

        return AppConfiguration(
            apiBaseURL: apiBaseURL,
            supportEmail: "tenimaletaapp@gmail.com",
            appName: "Castells en vena",
            appVersion: bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
                ?? "1.0",
            buildNumber: bundle.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1",
            technicalIdentifier: InstallationIdentifierStore(
                userDefaults: userDefaults
            ).currentIdentifier(),
            apnsEnvironment: apnsEnvironment,
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
        if let existing = userDefaults.string(forKey: key) { return existing }
        let identifier = UUID().uuidString
        userDefaults.set(identifier, forKey: key)
        return identifier
    }
}
