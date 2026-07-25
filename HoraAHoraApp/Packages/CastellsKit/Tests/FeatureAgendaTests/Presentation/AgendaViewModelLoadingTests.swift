import Foundation
import XCTest
@testable import FeatureAgenda

@MainActor
final class AgendaViewModelLoadingTests: XCTestCase {
    func testLoadPrefetchesSixMonthsBeforeAndAfterTheVisibleMonth() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")

        await model.load()

        XCTAssertEqual(model.events.map(\.title), ["Diada nativa"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-21", "2026-07-22"])
        XCTAssertEqual(model.sourceStatus, .active)
        XCTAssertEqual(repository.requestedLimit, 100)
        XCTAssertEqual(
            repository.requests.map { "\($0.from)|\($0.to)" },
            ["2026-01-01|2026-07-31", "2026-08-01|2027-01-31"]
        )
    }

    func testForceRefreshRefetchesTheWholePrefetchWindow() async {
        let repository = AgendaRepositoryStub()
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")
        await model.load()

        await model.load(forceRefresh: true)

        XCTAssertEqual(repository.requests.count, 4)
        XCTAssertEqual(repository.requests.prefix(2).map(\.forceRefresh), [false, false])
        XCTAssertEqual(repository.requests.suffix(2).map(\.forceRefresh), [true, true])
    }

    func testRefreshKeepsCurrentEventsVisibleAndOnlyReloadsTheVisibleMonth() async {
        let original = makeAgendaEvent(
            id: "original", localDate: "2026-07-21", title: "Diada desada"
        )
        let updated = makeAgendaEvent(
            id: "updated", localDate: "2026-07-21", title: "Diada actualitzada"
        )
        let neighboringMonth = makeAgendaEvent(
            id: "august", localDate: "2026-08-01", title: "Diada d'agost"
        )
        let repository = AgendaRepositoryStub(items: [original, neighboringMonth])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")
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
        model.selectedDate = agendaDate("2026-07-21")
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
        let cachedEvent = makeAgendaEvent(
            id: "cached", localDate: "2026-07-21", title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(
            cachedItems: [cachedEvent],
            remoteError: URLError(.notConnectedToInternet)
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")

        await model.load()

        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertTrue(model.isFromCache)
        XCTAssertNil(model.errorMessage)
        XCTAssertFalse(model.isLoading)
    }

    func testPreloadFromCacheHydratesTheAgendaWithoutStartingARequest() {
        let cachedEvent = makeAgendaEvent(
            id: "cached", localDate: "2026-07-21", title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(cachedItems: [cachedEvent])
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")

        model.preloadFromCache()

        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertEqual(model.monthEvents.map(\.title), ["Desada al dispositiu"])
        XCTAssertEqual(model.sourceStatus, .active)
        XCTAssertTrue(model.isFromCache)
        XCTAssertFalse(model.isLoading)
        XCTAssertTrue(repository.requests.isEmpty)
    }

    func testLoadReusesThePreloadedSnapshotWithoutReadingTheSameCacheWindowAgain() async {
        let cachedEvent = makeAgendaEvent(
            id: "cached", localDate: "2026-07-21", title: "Desada al dispositiu"
        )
        let repository = AgendaRepositoryStub(
            cachedItems: [cachedEvent],
            remoteError: URLError(.notConnectedToInternet)
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = agendaDate("2026-07-21")
        model.preloadFromCache()

        await model.load()

        XCTAssertEqual(repository.cachedRequests.count, 2)
        XCTAssertEqual(model.events.map(\.title), ["Desada al dispositiu"])
        XCTAssertNil(model.errorMessage)
        XCTAssertFalse(model.isLoading)
    }
}
