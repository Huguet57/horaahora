import Foundation
import XCTest
import CastellsDomain
@testable import FeatureAgenda

@MainActor
final class AgendaViewModelTests: XCTestCase {
    func testLoadPrefetchesSixMonthsBeforeAndAfterTheVisibleMonth() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = ISO8601DateFormatter().date(from: "2026-07-21T10:00:00Z")!

        await model.load()

        XCTAssertEqual(model.events.map(\.title), ["Diada nativa"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-21", "2026-07-22"])
        XCTAssertEqual(model.sourceStatus, .active)
        XCTAssertEqual(repository.requestedLimit, 100)
        XCTAssertEqual(
            repository.requests.map { "\($0.from)|\($0.to)" },
            [
                "2026-01-01|2026-07-31",
                "2026-08-01|2027-01-31"
            ]
        )
    }

    func testWeekStartsOnMondayAndCanCrossTheYearBoundary() {
        let dates = AgendaCalendarMath.week(containing: date("2027-01-01"))

        XCTAssertEqual(
            dates.map(localDate),
            [
                "2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31",
                "2027-01-01", "2027-01-02", "2027-01-03"
            ]
        )
    }

    func testPrefetchDeduplicatesEventsAndKeepsMonthEventsScopedToTheMonth() async {
        let repository = AgendaRepositoryStub(items: [
            makeEvent(id: "june", localDate: "2026-06-30", title: "Juny"),
            makeEvent(id: "july", localDate: "2026-07-21", title: "Juliol"),
            makeEvent(id: "july", localDate: "2026-07-21", title: "Duplicada"),
            makeEvent(id: "august", localDate: "2026-08-01", title: "Agost")
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")

        await model.load()

        XCTAssertEqual(model.monthEvents.map(\.title), ["Juliol"])
        XCTAssertEqual(model.eventDateKeys, ["2026-06-30", "2026-07-21", "2026-08-01"])
        XCTAssertEqual(model.events.map(\.title), ["Juliol"])
    }

    func testSelectingADayInAnotherMonthUsesPrefetchedDataAndExtendsTheWindow() async {
        let repository = AgendaRepositoryStub(items: [
            makeEvent(id: "july", localDate: "2026-07-31", title: "Juliol"),
            makeEvent(id: "august", localDate: "2026-08-01", title: "Agost")
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-31")
        await model.load()

        await model.selectAndLoad(date("2026-08-01"))

        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-02-01")
        XCTAssertEqual(repository.requestedTo, "2027-02-28")
        XCTAssertEqual(model.events.map(\.title), ["Agost"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Agost"])
        XCTAssertFalse(model.isLoading)

        await model.selectAndLoad(date("2026-08-02"))

        XCTAssertEqual(repository.requests.count, 3)
    }

    func testChangingWeekKeepsTheActiveDayAndExtendsThePrefetchWindowInTheBackground() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-28")
        await model.load()

        await model.changeWeek(by: 1)

        XCTAssertEqual(localDate(model.selectedDate), "2026-07-28")
        XCTAssertEqual(localDate(model.visibleWeek), "2026-08-04")
        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-02-01")
        XCTAssertEqual(repository.requestedTo, "2027-02-28")
        XCTAssertFalse(model.isLoading)
    }

    func testChangingMonthKeepsTheActiveDayAndExtendsThePrefetchWindow() async {
        let repository = AgendaRepositoryStub(items: [
            makeEvent(id: "december", localDate: "2026-12-21", title: "Desembre"),
            makeEvent(id: "january", localDate: "2027-01-21", title: "Gener")
        ])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-12-21")
        await model.load()

        await model.changeMonth(by: 1)

        XCTAssertEqual(localDate(model.selectedDate), "2026-12-21")
        XCTAssertEqual(localDate(model.visibleMonth), "2027-01-21")
        XCTAssertEqual(model.events.map(\.title), ["Desembre"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Gener"])
        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requestedFrom, "2027-07-01")
        XCTAssertEqual(repository.requestedTo, "2027-07-31")
        XCTAssertFalse(model.isLoading)
    }

    func testForceRefreshRefetchesTheWholePrefetchWindow() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")
        await model.load()

        await model.load(forceRefresh: true)

        XCTAssertEqual(repository.requests.count, 4)
        XCTAssertEqual(repository.requests.prefix(2).map(\.forceRefresh), [false, false])
        XCTAssertEqual(repository.requests.suffix(2).map(\.forceRefresh), [true, true])
    }

    func testRefreshKeepsCurrentEventsVisibleAndOnlyReloadsTheVisibleMonth() async {
        let original = makeEvent(
            id: "original",
            localDate: "2026-07-21",
            title: "Diada desada"
        )
        let updated = makeEvent(
            id: "updated",
            localDate: "2026-07-21",
            title: "Diada actualitzada"
        )
        let neighboringMonth = makeEvent(
            id: "august",
            localDate: "2026-08-01",
            title: "Diada d'agost"
        )
        let repository = AgendaRepositoryStub(items: [original, neighboringMonth])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")
        await model.load()
        repository.suspendNextForcedRefresh()

        let refresh = Task { await model.refresh() }
        while !repository.hasSuspendedRequest {
            await Task.yield()
        }

        XCTAssertEqual(model.events.map(\.title), ["Diada desada"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-21", "2026-08-01"])
        XCTAssertEqual(repository.requests.count, 3)
        XCTAssertEqual(repository.requests.last?.from, "2026-07-01")
        XCTAssertEqual(repository.requests.last?.to, "2026-07-31")
        XCTAssertEqual(repository.requests.last?.forceRefresh, true)

        repository.resumeSuspendedRequest(returning: [updated])
        await refresh.value

        XCTAssertEqual(model.events.map(\.title), ["Diada actualitzada"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-21", "2026-08-01"])
        XCTAssertFalse(model.isLoading)
    }

    func testRefreshDoesNotOverlapAnInFlightAgendaLoad() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")
        repository.suspendNextRequest()

        let initialLoad = Task { await model.load() }
        while !repository.hasSuspendedRequest {
            await Task.yield()
        }
        let requestsBeforeRefresh = repository.requests.count

        await model.refresh()

        XCTAssertEqual(repository.requests.count, requestsBeforeRefresh)
        XCTAssertFalse(repository.requests.contains(where: \.forceRefresh))

        repository.resumeSuspendedRequest()
        await initialLoad.value
    }

    func testLoadKeepsTheCachedSnapshotWhenSilentRevalidationFails() async {
        let cachedEvent = makeEvent(
            id: "cached",
            localDate: "2026-07-21",
            title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(
            cachedItems: [cachedEvent],
            remoteError: URLError(.notConnectedToInternet)
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")

        await model.load()

        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertTrue(model.isFromCache)
        XCTAssertNil(model.errorMessage)
        XCTAssertFalse(model.isLoading)
    }

    func testPreloadFromCacheHydratesTheAgendaWithoutStartingARequest() {
        let cachedEvent = makeEvent(
            id: "cached",
            localDate: "2026-07-21",
            title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(cachedItems: [cachedEvent])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")

        model.preloadFromCache()

        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Desada al dispositiu"])
        XCTAssertEqual(model.sourceStatus, .active)
        XCTAssertTrue(model.isFromCache)
        XCTAssertFalse(model.isLoading)
        XCTAssertTrue(repository.requests.isEmpty)
    }

    func testLoadReusesThePreloadedSnapshotWithoutReadingTheSameCacheWindowAgain() async {
        let cachedEvent = makeEvent(
            id: "cached",
            localDate: "2026-07-21",
            title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(
            cachedItems: [cachedEvent],
            remoteError: URLError(.notConnectedToInternet)
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = date("2026-07-21")
        model.preloadFromCache()

        await model.load()

        XCTAssertEqual(repository.cachedRequests.count, 2)
        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertNil(model.errorMessage)
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

    private func makeEvent(id: String, localDate: String, title: String) -> CastellEvent {
        CastellEvent(
            id: id, sourceID: "cccc", externalID: id, title: title,
            localDate: localDate, startsAt: nil, timeLabel: "Matí",
            timezone: "Europe/Madrid", venue: "Plaça", municipality: "Valls",
            participatingGroups: ["Colla A"], notes: "",
            sourceURL: URL(string: "https://castellscat.cat/ca/agenda")!,
            sourceOrder: 0,
            attribution: "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
            revision: "r1", updatedAt: Date()
        )
    }

    private func date(_ localDate: String) -> Date {
        let formatter = DateFormatter()
        formatter.calendar = AgendaCalendarMath.calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = AgendaCalendarMath.calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: localDate)!
    }

    private func localDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = AgendaCalendarMath.calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = AgendaCalendarMath.calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}

@MainActor
private final class AgendaRepositoryStub: AgendaRepository {
    let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!
    var requestedLimit: Int?
    var requestedFrom: String?
    var requestedTo: String?
    var requests: [(from: String, to: String, forceRefresh: Bool)] = []
    var cachedRequests: [(from: String, to: String)] = []
    private var suppliedItems: [CastellEvent]?
    private let suppliedCachedItems: [CastellEvent]
    private let remoteError: Error?
    private var shouldSuspendNextRequest = false
    private var onlySuspendForcedRefresh = false
    private var suspendedRequest: CheckedContinuation<Void, Never>?

    var hasSuspendedRequest: Bool {
        suspendedRequest != nil
    }

    init(
        items: [CastellEvent]? = nil,
        cachedItems: [CastellEvent] = [],
        remoteError: Error? = nil
    ) {
        suppliedItems = items
        suppliedCachedItems = cachedItems
        self.remoteError = remoteError
    }

    func suspendNextRequest() {
        shouldSuspendNextRequest = true
        onlySuspendForcedRefresh = false
    }

    func suspendNextForcedRefresh() {
        shouldSuspendNextRequest = true
        onlySuspendForcedRefresh = true
    }

    func resumeSuspendedRequest(returning items: [CastellEvent]? = nil) {
        if let items {
            suppliedItems = items
        }
        let continuation = suspendedRequest
        suspendedRequest = nil
        continuation?.resume()
    }

    func cachedEvents(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?
    ) throws -> [CastellEvent] {
        let lower = localDate(from)
        let upper = localDate(to)
        cachedRequests.append((from: lower, to: upper))
        return suppliedCachedItems.filter { lower <= $0.localDate && $0.localDate <= upper }
    }

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        if let remoteError { throw remoteError }
        requestedLimit = limit
        requestedFrom = localDate(from)
        requestedTo = localDate(to)
        requests.append((from: requestedFrom!, to: requestedTo!, forceRefresh: forceRefresh))
        if shouldSuspendNextRequest && (!onlySuspendForcedRefresh || forceRefresh) {
            shouldSuspendNextRequest = false
            await withCheckedContinuation { continuation in
                suspendedRequest = continuation
            }
        }
        let availableItems = suppliedItems ?? [
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
        ]
        let items = availableItems.filter {
            requestedFrom! <= $0.localDate && $0.localDate <= requestedTo!
        }
        return AgendaPage(
            items: items,
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
