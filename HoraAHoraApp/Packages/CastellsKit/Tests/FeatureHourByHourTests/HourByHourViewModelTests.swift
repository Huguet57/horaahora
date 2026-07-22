import Foundation
import XCTest
import CastellsDomain
@testable import FeatureHourByHour

@MainActor
final class HourByHourViewModelTests: XCTestCase {
    func testRefreshStaysVisibleLongEnoughToAcknowledgeTheGesture() async {
        let repository = SequencedHourByHourRepository(pages: [page(items: [])])
        let model = HourByHourViewModel(repository: repository)
        let clock = ContinuousClock()
        let startedAt = clock.now

        await model.refresh()

        let elapsed = startedAt.duration(to: clock.now)
        XCTAssertGreaterThanOrEqual(elapsed, .milliseconds(450))
        XCTAssertEqual(repository.requests.map(\.forceRefresh), [true])
        XCTAssertFalse(model.isLoading)
    }

    func testAutoRefreshLoadsThenRevalidatesWithoutForcingTheSource() async {
        let repository = SequencedHourByHourRepository(pages: [
            page(items: [item("first")]),
            page(items: [item("second"), item("first")]),
        ])
        let sleeper = SequencedSleeper(successfulSleeps: 1)
        let model = HourByHourViewModel(
            repository: repository,
            sleep: { duration in try await sleeper.sleep(duration) }
        )

        await model.runAutoRefresh(every: .seconds(60))

        XCTAssertEqual(repository.requests.map(\.forceRefresh), [false, false])
        XCTAssertEqual(sleeper.durations, [.seconds(60), .seconds(60)])
        XCTAssertEqual(model.items.map(\.id), ["second", "first"])
    }

    func testAutoRefreshRevalidatesImmediatelyWhenContentIsAlreadyLoaded() async {
        let repository = SequencedHourByHourRepository(pages: [
            page(items: [item("first")]),
            page(items: [item("second"), item("first")]),
        ])
        let sleeper = SequencedSleeper(successfulSleeps: 0)
        let model = HourByHourViewModel(
            repository: repository,
            sleep: { duration in try await sleeper.sleep(duration) }
        )
        await model.loadIfNeeded()

        await model.runAutoRefresh(every: .seconds(60))

        XCTAssertEqual(repository.requests.map(\.forceRefresh), [false, false])
        XCTAssertEqual(model.items.map(\.id), ["second", "first"])
    }

    func testRevalidationUpdatesEntriesWithoutDiscardingPagination() async {
        let repository = SequencedHourByHourRepository(pages: [
            page(
                items: [item("newest"), item("middle", title: "Original")],
                nextCursor: "page-2"
            ),
            page(items: [item("old")], nextCursor: "page-3"),
            page(
                items: [
                    item("brand-new"),
                    item("newest"),
                    item("middle", title: "Actualitzat"),
                ],
                nextCursor: "fresh-page-2"
            ),
            page(items: [item("oldest")]),
        ])
        let model = HourByHourViewModel(repository: repository)

        await model.loadIfNeeded()
        await model.loadNextIfNeeded(after: model.items.last!)
        await model.revalidate()

        XCTAssertEqual(model.items.map(\.id), ["brand-new", "newest", "middle", "old"])
        XCTAssertEqual(model.items.first(where: { $0.id == "middle" })?.title, "Actualitzat")

        await model.loadNextIfNeeded(after: model.items.last!)

        XCTAssertEqual(repository.requests.map(\.cursor), [nil, "page-2", nil, "page-3"])
        XCTAssertEqual(
            model.items.map(\.id),
            ["brand-new", "newest", "middle", "old", "oldest"]
        )
    }

    func testRevalidationDoesNotOverlapAnInFlightLoad() async {
        let repository = SuspendingHourByHourRepository(result: page(items: [item("first")]))
        let model = HourByHourViewModel(repository: repository)

        let initialLoad = Task { await model.loadIfNeeded() }
        while repository.requests.isEmpty {
            await Task.yield()
        }

        await model.revalidate()

        XCTAssertEqual(repository.requests.count, 1)
        repository.resume()
        await initialLoad.value
    }

    func testAutoRefreshStopsWhenItsTaskIsCancelled() async {
        let repository = SequencedHourByHourRepository(pages: [page(items: [item("first")])])
        let sleepProbe = SleepProbe()
        let model = HourByHourViewModel(
            repository: repository,
            sleep: { duration in
                await sleepProbe.markStarted()
                try await Task.sleep(for: duration)
            }
        )

        let refreshTask = Task { await model.runAutoRefresh(every: .seconds(60)) }
        while !(await sleepProbe.hasStarted) {
            await Task.yield()
        }
        refreshTask.cancel()
        await refreshTask.value

        XCTAssertEqual(repository.requests.count, 1)
    }

    private func page(
        items: [HourByHourItem],
        nextCursor: String? = nil
    ) -> HourByHourPage {
        HourByHourPage(items: items, nextCursor: nextCursor, fromCache: false)
    }

    private func item(_ id: String, title: String? = nil) -> HourByHourItem {
        let timestamp = Date(timeIntervalSince1970: 1_700_000_000)
        return HourByHourItem(
            id: id,
            sourceID: "revista-castells",
            externalID: id,
            title: title ?? id,
            displayTitle: title ?? id,
            summary: "",
            publishedAt: timestamp,
            sourceOrder: 0,
            articleURL: URL(string: "https://example.com/\(id)")!,
            actionURL: nil,
            attribution: "Revista Castells",
            createdAt: timestamp,
            updatedAt: timestamp
        )
    }
}

@MainActor
private final class SequencedHourByHourRepository: HourByHourRepository {
    struct Request {
        let cursor: String?
        let forceRefresh: Bool
    }

    private var pages: [HourByHourPage]
    private(set) var requests: [Request] = []

    init(pages: [HourByHourPage]) {
        self.pages = pages
    }

    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        requests.append(Request(cursor: cursor, forceRefresh: forceRefresh))
        guard !pages.isEmpty else { throw StubError.missingPage }
        return pages.removeFirst()
    }
}

@MainActor
private final class SuspendingHourByHourRepository: HourByHourRepository {
    private let result: HourByHourPage
    private var continuation: CheckedContinuation<Void, Never>?
    private(set) var requests: [Bool] = []

    init(result: HourByHourPage) {
        self.result = result
    }

    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        requests.append(forceRefresh)
        await withCheckedContinuation { continuation in
            self.continuation = continuation
        }
        return result
    }

    func resume() {
        continuation?.resume()
        continuation = nil
    }
}

@MainActor
private final class SequencedSleeper {
    private var successfulSleeps: Int
    private(set) var durations: [Duration] = []

    init(successfulSleeps: Int) {
        self.successfulSleeps = successfulSleeps
    }

    func sleep(_ duration: Duration) async throws {
        durations.append(duration)
        guard successfulSleeps > 0 else { throw CancellationError() }
        successfulSleeps -= 1
    }
}

private actor SleepProbe {
    private var started = false

    var hasStarted: Bool { started }

    func markStarted() {
        started = true
    }
}

private enum StubError: Error {
    case missingPage
}
