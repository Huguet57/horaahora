import Foundation
import XCTest
import CastellsDomain
@testable import FeatureAgenda

@MainActor
final class AgendaViewModelTests: XCTestCase {
    func testLoadsTheWholeMonthAndExposesDaysWithEvents() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = ISO8601DateFormatter().date(from: "2026-07-21T10:00:00Z")!

        await model.load()

        XCTAssertEqual(model.events.map(\.title), ["Diada nativa"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-21", "2026-07-22"])
        XCTAssertEqual(model.sourceStatus, .active)
        XCTAssertEqual(repository.requestedLimit, 100)
        XCTAssertEqual(repository.requestedFrom, "2026-07-01")
        XCTAssertEqual(repository.requestedTo, "2026-07-31")
    }

    func testGoogleMapsURLSearchesForVenueAndMunicipality() throws {
        let url = try XCTUnwrap(
            googleMapsSearchURL(venue: "Plaça Vella", municipality: "El Vendrell")
        )
        let components = try XCTUnwrap(URLComponents(url: url, resolvingAgainstBaseURL: false))

        XCTAssertEqual(components.scheme, "https")
        XCTAssertEqual(components.host, "www.google.com")
        XCTAssertEqual(components.path, "/maps/search/")
        XCTAssertEqual(components.queryItems?.first(where: { $0.name == "api" })?.value, "1")
        XCTAssertEqual(
            components.queryItems?.first(where: { $0.name == "query" })?.value,
            "Plaça Vella, El Vendrell"
        )
    }
}

@MainActor
private final class AgendaRepositoryStub: AgendaRepository {
    let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!
    var requestedLimit: Int?
    var requestedFrom: String?
    var requestedTo: String?

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        requestedLimit = limit
        requestedFrom = localDate(from)
        requestedTo = localDate(to)
        return AgendaPage(
            items: [
                CastellEvent(
                    id: "1", sourceID: "cccc", externalID: "1", title: "Diada nativa",
                    localDate: "2026-07-21", startsAt: nil, timeLabel: "Matí",
                    timezone: "Europe/Madrid", venue: "Plaça", municipality: "Valls",
                    participatingGroups: ["Colla A"], notes: "", sourceURL: officialURL,
                    sourceOrder: 0,
                    attribution: "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                    revision: "r1", updatedAt: Date()
                ),
                CastellEvent(
                    id: "2", sourceID: "cccc", externalID: "2", title: "Diada següent",
                    localDate: "2026-07-22", startsAt: nil, timeLabel: "Tarda",
                    timezone: "Europe/Madrid", venue: "Plaça", municipality: "Tarragona",
                    participatingGroups: ["Colla B"], notes: "", sourceURL: officialURL,
                    sourceOrder: 1,
                    attribution: "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                    revision: "r1", updatedAt: Date()
                )
            ],
            nextCursor: nil, officialURL: officialURL, fromCache: false, sourceStatus: .active
        )
    }

    private func localDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Europe/Madrid")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}
