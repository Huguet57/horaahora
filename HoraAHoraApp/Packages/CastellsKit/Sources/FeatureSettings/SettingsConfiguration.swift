import Foundation

public struct SettingsConfiguration: Equatable, Sendable {
    public let apiBaseURL: URL
    public let supportEmail: String
    public let appName: String
    public let appVersion: String
    public let buildNumber: String
    public let technicalIdentifier: String
    public let revistaCastellsURL: URL?
    public let ccccAgendaURL: URL?
    public let concursCastellsURL: URL?

    public init(
        apiBaseURL: URL,
        supportEmail: String,
        appName: String,
        appVersion: String,
        buildNumber: String,
        technicalIdentifier: String,
        revistaCastellsURL: URL?,
        ccccAgendaURL: URL?,
        concursCastellsURL: URL?
    ) {
        self.apiBaseURL = apiBaseURL
        self.supportEmail = supportEmail
        self.appName = appName
        self.appVersion = appVersion
        self.buildNumber = buildNumber
        self.technicalIdentifier = technicalIdentifier
        self.revistaCastellsURL = revistaCastellsURL
        self.ccccAgendaURL = ccccAgendaURL
        self.concursCastellsURL = concursCastellsURL
    }

    public var privacyURL: URL {
        apiBaseURL.appending(path: "privacy")
    }

    public var supportEmailURL: URL {
        var components = URLComponents()
        components.scheme = "mailto"
        components.path = supportEmail
        components.queryItems = [
            URLQueryItem(name: "subject", value: "Suport \(appName)"),
            URLQueryItem(name: "body", value: supportEmailBody),
        ]
        guard let url = components.url else {
            preconditionFailure("L'adreça de suport configurada no és vàlida")
        }
        return url
    }

    public var versionAndBuild: String {
        "Versió \(appVersion) (\(buildNumber))"
    }

    private var supportEmailBody: String {
        """
        Hola,

        Explica'ns com et podem ajudar:


        ---
        Informació tècnica (la pots revisar i editar abans d'enviar el correu)
        Versió: \(appVersion) (\(buildNumber))
        Identificador tècnic: \(technicalIdentifier)
        """
    }
}
