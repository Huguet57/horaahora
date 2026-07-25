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
    public private(set) var events: [CastellEvent] = []
    public private(set) var otherEvents: [CastellEvent] = []
    public private(set) var eventDateKeys: Set<String> = []
    var eventWindow = AgendaEventWindow()
    private var monthsBeingPrefetched: Set<String> = []
    private var hasStartedInitialLoad = false
    private var isLoadInFlight = false
    public private(set) var isLoading = false
    public private(set) var errorMessage: String?
    public private(set) var isFromCache = false
    public private(set) var sourceStatus: AgendaSourceStatus = .unavailable
    public internal(set) var groupDirectoryErrorMessage: String?
    public let officialURL: URL
    let repository: any AgendaRepository
    private let pageLoader: AgendaPageLoader
    private let cacheReader: AgendaCacheWindowReader
    var groupFilter: AgendaGroupFilter

    public init(
        repository: any AgendaRepository,
        filterStore: (any AgendaFilterStoring)? = nil
    ) {
        let now = Date()
        self.selectedDate = now
        self.visibleMonth = now
        self.visibleWeek = now
        self.repository = repository
        self.pageLoader = AgendaPageLoader(repository: repository)
        self.cacheReader = AgendaCacheWindowReader(repository: repository)
        self.officialURL = repository.officialURL
        self.groupFilter = AgendaGroupFilter(store: filterStore)
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
        guard !isLoadInFlight else { return }
        isLoadInFlight = true
        defer { isLoadInFlight = false }

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
            let results: [AgendaFetchResult]
            if ranges.count == 2 {
                async let first = pageLoader.fetch(range: ranges[0], forceRefresh: forceRefresh)
                async let second = pageLoader.fetch(range: ranges[1], forceRefresh: forceRefresh)
                let pair = try await (first, second)
                results = [pair.0, pair.1]
            } else {
                var sequentialResults: [AgendaFetchResult] = []
                for range in ranges {
                    sequentialResults.append(
                        try await pageLoader.fetch(range: range, forceRefresh: forceRefresh)
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
            cacheReader.reset()
        } catch {
            if !hasCachedSnapshot {
                errorMessage = error.localizedDescription
            }
        }
    }

    public func refresh() async {
        guard
            !isLoadInFlight,
            let range = AgendaCalendarMath.monthRange(containing: visibleMonth)
        else {
            return
        }
        isLoadInFlight = true
        defer { isLoadInFlight = false }
        errorMessage = nil

        do {
            let result = try await pageLoader.fetch(range: range, forceRefresh: true)
            applyPrefetchedWindow(
                from: range.start,
                through: range.end,
                items: result.items,
                sourceStatus: result.sourceStatus,
                fromCache: result.fromCache
            )
            cacheReader.reset()
        } catch {
            if eventWindow.isEmpty {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func restoreCachedSnapshot(
        in ranges: [(start: Date, end: Date)]
    ) -> Bool {
        let lookup = cacheReader.lookup(in: ranges)
        if let window = lookup.windowToApply {
            applyPrefetchedWindow(
                from: window.start,
                through: window.end,
                items: window.items,
                sourceStatus: .active,
                fromCache: true
            )
        }
        return lookup.hasSnapshot
    }

    private func extendPrefetchWindowIfNeeded(containing date: Date) async {
        let desiredRanges = AgendaCalendarMath.prefetchRanges(containing: date)
        guard let firstRange = desiredRanges.first, let lastRange = desiredRanges.last else { return }

        let missingMonths = AgendaCalendarMath.monthStarts(
            from: firstRange.start,
            through: lastRange.end
        ).filter {
            let key = AgendaCalendarMath.monthKey($0)
            return !eventWindow.containsMonth($0) && !monthsBeingPrefetched.contains(key)
        }

        for monthStart in missingMonths {
            let key = AgendaCalendarMath.monthKey(monthStart)
            guard let range = AgendaCalendarMath.monthRange(containing: monthStart) else { continue }
            monthsBeingPrefetched.insert(key)
            do {
                let result = try await pageLoader.fetch(range: range, forceRefresh: false)
                eventWindow.replace(from: range.start, through: range.end, with: result.items)
                eventWindow.markLoaded(monthStartingAt: monthStart)
                mergeObservedGroups()
                updateVisibleMonthEvents()
            } catch {
                // The selected month is already in the prefetched window. A failed edge
                // extension is retried on a later navigation without interrupting the UI.
            }
            monthsBeingPrefetched.remove(key)
        }
    }

    private func applyPrefetchedWindow(
        from start: Date,
        through end: Date,
        items: [CastellEvent],
        sourceStatus: AgendaSourceStatus,
        fromCache: Bool
    ) {
        eventWindow.replace(from: start, through: end, with: items)
        eventWindow.markLoaded(from: start, through: end)
        mergeObservedGroups()
        self.sourceStatus = sourceStatus
        isFromCache = fromCache
        updateVisibleMonthEvents()
    }

    func updateVisibleMonthEvents() {
        let dayEvents = eventWindow.events(on: selectedDate)
        events = dayEvents.filter(matchesGroupSelection)
        otherEvents = dayEvents.filter { !matchesGroupSelection($0) }
        eventDateKeys = eventWindow.dateKeys(matching: matchesGroupSelection)
        monthEvents = eventWindow.events(inMonthContaining: visibleMonth)
            .filter(matchesGroupSelection)
    }

    func matchesGroupSelection(_ event: CastellEvent) -> Bool {
        groupFilter.matches(participatingGroups: event.participatingGroups)
    }
}
