import Foundation
import CastellsDomain

func page(
    items: [HourByHourItem],
    nextCursor: String? = nil
) -> HourByHourPage {
    HourByHourPage(items: items, nextCursor: nextCursor, fromCache: false)
}

func item(
    _ id: String,
    title: String? = nil,
    publishedAt: Date? = nil,
    sourceID: String = "revista-castells",
    externalID: String? = nil
) -> HourByHourItem {
    let timestamp = publishedAt ?? Date(timeIntervalSince1970: 1_700_000_000)
    return HourByHourItem(
        id: id,
        sourceID: sourceID,
        externalID: externalID ?? id,
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

@MainActor
final class SequencedHourByHourRepository: HourByHourRepository {
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
final class SuspendingHourByHourRepository: HourByHourRepository {
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
final class SequencedSleeper {
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

actor SleepProbe {
    private var started = false

    var hasStarted: Bool { started }

    func markStarted() {
        started = true
    }
}

enum StubError: Error {
    case missingPage
}
