import Foundation
import FeatureSettings

/// Where Hora a Hora and Agenda take their data from, credited while those sections show.
public struct InternalSources: Equatable, Sendable {
    public let revistaCastellsURL: URL?
    public let elMonCastellerURL: URL?
    public let ccccAgendaURL: URL?

    public init(revistaCastellsURL: URL?, elMonCastellerURL: URL?, ccccAgendaURL: URL?) {
        self.revistaCastellsURL = revistaCastellsURL
        self.elMonCastellerURL = elMonCastellerURL
        self.ccccAgendaURL = ccccAgendaURL
    }

    public var credits: [SettingsCredit] {
        [
            SettingsCredit(
                name: "Revista Castells",
                detail: "Font de l'Hora a Hora",
                url: revistaCastellsURL
            ),
            SettingsCredit(
                name: "El Món Casteller",
                detail: "Notícies, opinió, entrevistes i cròniques de l'Hora a Hora",
                url: elMonCastellerURL
            ),
            SettingsCredit(
                name: "Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                detail: "Font de l'Agenda",
                url: ccccAgendaURL
            ),
        ]
    }
}
