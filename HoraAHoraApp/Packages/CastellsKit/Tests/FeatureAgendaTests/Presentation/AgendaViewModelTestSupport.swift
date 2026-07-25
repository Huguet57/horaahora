import Foundation
import CastellsDomain
@testable import FeatureAgenda

@MainActor
final class AgendaRepositoryStub: AgendaRepository {
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
        let lower = agendaLocalDate(from)
        let upper = agendaLocalDate(to)
        cachedRequests.append((from: lower, to: upper))
        return suppliedCachedItems.filter { lower <= $0.localDate && $0.localDate <= upper }
    }

    func events(
        from: Date, to: Date, group: String?, municipality: String?, cursor: String?,
        limit: Int, forceRefresh: Bool
    ) async throws -> AgendaPage {
        if let remoteError { throw remoteError }
        requestedLimit = limit
        requestedFrom = agendaLocalDate(from)
        requestedTo = agendaLocalDate(to)
        requests.append((from: requestedFrom!, to: requestedTo!, forceRefresh: forceRefresh))
        if shouldSuspendNextRequest && (!onlySuspendForcedRefresh || forceRefresh) {
            shouldSuspendNextRequest = false
            await withCheckedContinuation { continuation in
                suspendedRequest = continuation
            }
        }
        let availableItems = suppliedItems ?? [
            makeAgendaEvent(id: "1", localDate: "2026-07-21", title: "Diada nativa"),
            makeAgendaEvent(
                id: "2",
                localDate: "2026-07-22",
                title: "Diada següent",
                municipality: "Tarragona",
                sourceOrder: 1
            ),
        ]
        let items = availableItems.filter {
            requestedFrom! <= $0.localDate && $0.localDate <= requestedTo!
        }
        return AgendaPage(
            items: items,
            nextCursor: nil,
            officialURL: officialURL,
            fromCache: false,
            sourceStatus: .active
        )
    }
}

func makeAgendaEvent(
    id: String,
    localDate: String,
    title: String,
    municipality: String = "Valls",
    sourceOrder: Int = 0,
    participatingGroups: [String] = ["Colla A"]
) -> CastellEvent {
    CastellEvent(
        id: id,
        sourceID: "cccc",
        externalID: id,
        title: title,
        localDate: localDate,
        startsAt: nil,
        timeLabel: "Matí",
        timezone: "Europe/Madrid",
        venue: "Plaça",
        municipality: municipality,
        participatingGroups: participatingGroups,
        notes: "",
        sourceURL: URL(string: "https://castellscat.cat/ca/agenda")!,
        sourceOrder: sourceOrder,
        attribution: "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
        revision: "r1",
        updatedAt: Date()
    )
}

func agendaDate(_ localDate: String) -> Date {
    let formatter = DateFormatter()
    formatter.calendar = AgendaCalendarMath.calendar
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = AgendaCalendarMath.calendar.timeZone
    formatter.dateFormat = "yyyy-MM-dd"
    return formatter.date(from: localDate)!
}

func agendaLocalDate(_ date: Date) -> String {
    AgendaCalendarMath.localDateKey(date)
}
