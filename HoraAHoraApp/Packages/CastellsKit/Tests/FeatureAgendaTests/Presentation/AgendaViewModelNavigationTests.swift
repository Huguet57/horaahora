import Foundation
import XCTest
@testable import FeatureAgenda

@MainActor
final class AgendaViewModelNavigationTests: XCTestCase {
    func testWeekStartsOnMondayAndCanCrossTheYearBoundary() {
        let dates = AgendaCalendarMath.week(containing: agendaDate("2027-01-01"))

        XCTAssertEqual(
            dates.map(agendaLocalDate),
            [
                "2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31",
                "2027-01-01", "2027-01-02", "2027-01-03",
            ]
        )
    }

    func testPrefetchDeduplicatesEventsAndKeepsMonthEventsScopedToTheMonth() async {
        let repository = AgendaRepositoryStub(items: [
            makeAgendaEvent(id: "june", localDate: "2026-06-30", title: "Juny"),
            makeAgendaEvent(id: "july", localDate: "2026-07-21", title: "Juliol"),
            makeAgendaEvent(id: "july", localDate: "2026-07-21", title: "Duplicada"),
            makeAgendaEvent(id: "august", localDate: "2026-08-01", title: "Agost"),
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")

        await model.load()

        XCTAssertEqual(model.monthEvents.map(\.title), ["Juliol"])
        XCTAssertEqual(model.eventDateKeys, ["2026-06-30", "2026-07-21", "2026-08-01"])
        XCTAssertEqual(model.events.map(\.title), ["Juliol"])
    }

    func testSelectingADayInAnotherMonthUsesPrefetchedDataAndExtendsTheWindow() async {
        let repository = AgendaRepositoryStub(items: [
            makeAgendaEvent(id: "july", localDate: "2026-07-31", title: "Juliol"),
            makeAgendaEvent(id: "august", localDate: "2026-08-01", title: "Agost"),
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-31")
        await model.load()

        await model.selectAndLoad(agendaDate("2026-08-01"))

        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-02-01")
        XCTAssertEqual(repository.requestedTo, "2027-02-28")
        XCTAssertEqual(model.events.map(\.title), ["Agost"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Agost"])
        XCTAssertFalse(model.isLoading)

        await model.selectAndLoad(agendaDate("2026-08-02"))
        XCTAssertEqual(repository.requests.count, 3)
    }

    func testChangingWeekKeepsTheActiveDayAndExtendsThePrefetchWindowInTheBackground() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-28")
        await model.load()

        await model.changeWeek(by: 1)

        XCTAssertEqual(agendaLocalDate(model.selectedDate), "2026-07-28")
        XCTAssertEqual(agendaLocalDate(model.visibleWeek), "2026-08-04")
        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-02-01")
        XCTAssertEqual(repository.requestedTo, "2027-02-28")
        XCTAssertFalse(model.isLoading)
    }

    func testChangingMonthKeepsTheActiveDayAndExtendsThePrefetchWindow() async {
        let repository = AgendaRepositoryStub(items: [
            makeAgendaEvent(id: "december", localDate: "2026-12-21", title: "Desembre"),
            makeAgendaEvent(id: "january", localDate: "2027-01-21", title: "Gener"),
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-12-21")
        await model.load()

        await model.changeMonth(by: 1)

        XCTAssertEqual(agendaLocalDate(model.selectedDate), "2026-12-21")
        XCTAssertEqual(agendaLocalDate(model.visibleMonth), "2027-01-21")
        XCTAssertEqual(model.events.map(\.title), ["Desembre"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Gener"])
        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-07-01")
        XCTAssertEqual(repository.requestedTo, "2027-07-31")
        XCTAssertFalse(model.isLoading)
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
