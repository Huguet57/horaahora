import Foundation
import Observation
import CastellsDomain

@MainActor
@Observable
public final class AgendaViewModel {
    public var selectedDate: Date
    public private(set) var visibleMonth: Date
    public private(set) var visibleWeek: Date
    public private(set) var monthEvents: [CastellEvent] = []
    private var prefetchedEvents: [CastellEvent] = []
    private var prefetchedMonthKeys: Set<String> = []
    private var monthsBeingPrefetched: Set<String> = []
    private var hasStartedInitialLoad = false
    private var cachedWindowState: CachedWindowState?
    public private(set) var isLoading = false
    public private(set) var errorMessage: String?
    public private(set) var isFromCache = false
    public private(set) var sourceStatus: AgendaSourceStatus = .unavailable
    public let officialURL: URL
    private let repository: any AgendaRepository

    public init(repository: any AgendaRepository) {
        let now = Date()
        self.selectedDate = now
        self.visibleMonth = now
        self.visibleWeek = now
        self.repository = repository
        self.officialURL = repository.officialURL
    }

    public var events: [CastellEvent] {
        let selectedKey = AgendaCalendarMath.localDateKey(selectedDate)
        return prefetchedEvents.filter { $0.localDate == selectedKey }
    }

    public var eventDateKeys: Set<String> {
        Set(prefetchedEvents.map(\.localDate))
    }

    public func preloadFromCache() {
        if !hasStartedInitialLoad {
            visibleMonth = selectedDate
            visibleWeek = selectedDate
        }
        let ranges = AgendaCalendarMath.prefetchRanges(containing: visibleMonth)
        _ = restoreCachedSnapshot(in: ranges)
    }

    public func select(_ date: Date) {
        selectedDate = date
        visibleMonth = date
        visibleWeek = date
        updateVisibleMonthEvents()
    }

    public func selectAndLoad(_ date: Date) async {
        select(date)
        await extendPrefetchWindowIfNeeded(containing: date)
    }

    public func changeMonth(by offset: Int) async {
        guard let date = AgendaCalendarMath.calendar.date(
            byAdding: .month,
            value: offset,
            to: visibleMonth
        ) else {
            return
        }
        visibleMonth = date
        updateVisibleMonthEvents()
        await extendPrefetchWindowIfNeeded(containing: date)
    }

    public func changeWeek(by offset: Int) async {
        guard let date = AgendaCalendarMath.calendar.date(
            byAdding: .day,
            value: offset * 7,
            to: visibleWeek
        ) else {
            return
        }
        visibleWeek = date
        await extendPrefetchWindowIfNeeded(containing: date)
    }

    public func load(forceRefresh: Bool = false) async {
        errorMessage = nil
        if !hasStartedInitialLoad {
            visibleMonth = selectedDate
            visibleWeek = selectedDate
            hasStartedInitialLoad = true
        }
        let ranges = AgendaCalendarMath.prefetchRanges(containing: visibleMonth)
        guard let firstRange = ranges.first, let lastRange = ranges.last else { return }

        let hasCachedSnapshot = forceRefresh ? false : restoreCachedSnapshot(in: ranges)
        isLoading = !hasCachedSnapshot
        defer { isLoading = false }

        do {
            let results: [FetchResult]
            if ranges.count == 2 {
                async let first = fetch(range: ranges[0], forceRefresh: forceRefresh)
                async let second = fetch(range: ranges[1], forceRefresh: forceRefresh)
                let pair = try await (first, second)
                results = [pair.0, pair.1]
            } else {
                var sequentialResults: [FetchResult] = []
                for range in ranges {
                    sequentialResults.append(
                        try await fetch(range: range, forceRefresh: forceRefresh)
                    )
                }
                results = sequentialResults
            }

            applyPrefetchedWindow(
                from: firstRange.start,
                through: lastRange.end,
                items: results.flatMap(\.items),
                sourceStatus: results.allSatisfy { $0.sourceStatus == .active }
                    ? .active
                    : .unavailable,
                fromCache: results.allSatisfy(\.fromCache)
            )
            cachedWindowState = nil
        } catch {
            if !hasCachedSnapshot {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func restoreCachedSnapshot(
        in ranges: [(start: Date, end: Date)]
    ) -> Bool {
        guard let firstRange = ranges.first, let lastRange = ranges.last else { return false }
        let window = CachedWindowState(
            startKey: AgendaCalendarMath.localDateKey(firstRange.start),
            endKey: AgendaCalendarMath.localDateKey(lastRange.end),
            hasSnapshot: false
        )
        if let cachedWindowState,
           cachedWindowState.startKey == window.startKey,
           cachedWindowState.endKey == window.endKey {
            return cachedWindowState.hasSnapshot
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
        cachedWindowState = CachedWindowState(
            startKey: window.startKey,
            endKey: window.endKey,
            hasSnapshot: hasSnapshot
        )
        guard hasSnapshot else { return false }

        applyPrefetchedWindow(
            from: firstRange.start,
            through: lastRange.end,
            items: cached,
            sourceStatus: .active,
            fromCache: true
        )
        return true
    }

    private func extendPrefetchWindowIfNeeded(containing date: Date) async {
        let desiredRanges = AgendaCalendarMath.prefetchRanges(containing: date)
        guard let firstRange = desiredRanges.first, let lastRange = desiredRanges.last else { return }

        let missingMonths = AgendaCalendarMath.monthStarts(
            from: firstRange.start,
            through: lastRange.end
        ).filter {
            let key = AgendaCalendarMath.monthKey($0)
            return !prefetchedMonthKeys.contains(key) && !monthsBeingPrefetched.contains(key)
        }

        for monthStart in missingMonths {
            let key = AgendaCalendarMath.monthKey(monthStart)
            guard let range = AgendaCalendarMath.monthRange(containing: monthStart) else { continue }
            monthsBeingPrefetched.insert(key)
            do {
                let result = try await fetch(range: range, forceRefresh: false)
                replacePrefetchedEvents(from: range.start, through: range.end, with: result.items)
                prefetchedMonthKeys.insert(key)
                updateVisibleMonthEvents()
            } catch {
                // The selected month is already in the prefetched window. A failed edge
                // extension is retried on a later navigation without interrupting the UI.
            }
            monthsBeingPrefetched.remove(key)
        }
    }

    private typealias FetchResult = (
        items: [CastellEvent],
        fromCache: Bool,
        sourceStatus: AgendaSourceStatus
    )

    private struct CachedWindowState {
        let startKey: String
        let endKey: String
        let hasSnapshot: Bool
    }

    private func fetch(
        range: (start: Date, end: Date),
        forceRefresh: Bool
    ) async throws -> FetchResult {
        var cursor: String?
        var collected: [CastellEvent] = []
        var allFromCache = true
        var statuses: [AgendaSourceStatus] = []

        repeat {
            let page = try await repository.events(
                from: range.start,
                to: range.end,
                group: nil,
                municipality: nil,
                cursor: cursor,
                limit: 100,
                forceRefresh: forceRefresh && cursor == nil
            )
            collected.append(contentsOf: page.items)
            allFromCache = allFromCache && page.fromCache
            statuses.append(page.sourceStatus)
            cursor = page.nextCursor
        } while cursor != nil

        return (
            uniqueAndSorted(collected),
            allFromCache,
            statuses.allSatisfy { $0 == .active } ? .active : .unavailable
        )
    }

    private func applyPrefetchedWindow(
        from start: Date,
        through end: Date,
        items: [CastellEvent],
        sourceStatus: AgendaSourceStatus,
        fromCache: Bool
    ) {
        replacePrefetchedEvents(from: start, through: end, with: items)
        prefetchedMonthKeys.formUnion(
            AgendaCalendarMath.monthStarts(from: start, through: end)
                .map(AgendaCalendarMath.monthKey)
        )
        self.sourceStatus = sourceStatus
        isFromCache = fromCache
        updateVisibleMonthEvents()
    }

    private func replacePrefetchedEvents(
        from start: Date,
        through end: Date,
        with events: [CastellEvent]
    ) {
        let lower = AgendaCalendarMath.localDateKey(start)
        let upper = AgendaCalendarMath.localDateKey(end)
        prefetchedEvents.removeAll { lower <= $0.localDate && $0.localDate <= upper }
        prefetchedEvents.append(contentsOf: events)
        prefetchedEvents = uniqueAndSorted(prefetchedEvents)
    }

    private func uniqueAndSorted(_ events: [CastellEvent]) -> [CastellEvent] {
        var seen = Set<String>()
        return events
            .filter { seen.insert("\($0.sourceID):\($0.externalID)").inserted }
            .sorted {
                if $0.localDate == $1.localDate { return $0.sourceOrder < $1.sourceOrder }
                return $0.localDate < $1.localDate
            }
    }

    private func updateVisibleMonthEvents() {
        guard let range = AgendaCalendarMath.monthRange(containing: visibleMonth) else {
            monthEvents = []
            return
        }
        let lower = AgendaCalendarMath.localDateKey(range.start)
        let upper = AgendaCalendarMath.localDateKey(range.end)
        monthEvents = prefetchedEvents.filter { lower <= $0.localDate && $0.localDate <= upper }
    }
}
