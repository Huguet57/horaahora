import Foundation
import CastellsDomain

struct AgendaCachedWindow {
    let start: Date
    let end: Date
    let items: [CastellEvent]
}

struct AgendaCacheLookup {
    let hasSnapshot: Bool
    let windowToApply: AgendaCachedWindow?
}

@MainActor
final class AgendaCacheWindowReader {
    private struct State {
        let startKey: String
        let endKey: String
        let hasSnapshot: Bool
    }

    private let repository: any AgendaRepository
    private var state: State?

    init(repository: any AgendaRepository) {
        self.repository = repository
    }

    func lookup(in ranges: [(start: Date, end: Date)]) -> AgendaCacheLookup {
        guard let firstRange = ranges.first, let lastRange = ranges.last else {
            return AgendaCacheLookup(hasSnapshot: false, windowToApply: nil)
        }
        let requestedState = State(
            startKey: AgendaCalendarMath.localDateKey(firstRange.start),
            endKey: AgendaCalendarMath.localDateKey(lastRange.end),
            hasSnapshot: false
        )
        if let state,
           state.startKey == requestedState.startKey,
           state.endKey == requestedState.endKey {
            return AgendaCacheLookup(hasSnapshot: state.hasSnapshot, windowToApply: nil)
        }

        let cached = ranges.flatMap { range in
            (try? repository.cachedEvents(
                from: range.start,
                to: range.end,
                group: nil,
                municipality: nil
            )) ?? []
        }
        let hasSnapshot = !cached.isEmpty
        state = State(
            startKey: requestedState.startKey,
            endKey: requestedState.endKey,
            hasSnapshot: hasSnapshot
        )
        return AgendaCacheLookup(
            hasSnapshot: hasSnapshot,
            windowToApply: hasSnapshot
                ? AgendaCachedWindow(start: firstRange.start, end: lastRange.end, items: cached)
                : nil
        )
    }

    func reset() {
        state = nil
    }
}
