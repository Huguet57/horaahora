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
    private var eventWindow = AgendaEventWindow()
    private var monthsBeingPrefetched: Set<String> = []
    private var hasStartedInitialLoad = false
    private var isLoadInFlight = false
    public private(set) var isLoading = false
    public private(set) var errorMessage: String?
    public private(set) var isFromCache = false
    public private(set) var sourceStatus: AgendaSourceStatus = .unavailable
    public private(set) var groupDirectoryErrorMessage: String?
    public let officialURL: URL
    private let repository: any AgendaRepository
    private let pageLoader: AgendaPageLoader
    private let cacheReader: AgendaCacheWindowReader
    private let filterStore: (any AgendaFilterStoring)?
    private var groupSelection: AgendaGroupSelection
    private var featuredGroupKeys: Set<String>
    private var knownGroups: [String]
    private var directoryRevision: String?

    public init(
        repository: any AgendaRepository,
        filterStore: (any AgendaFilterStoring)? = nil
    ) {
        let now = Date()
        let persisted = filterStore?.load() ?? AgendaFilterState()
        self.selectedDate = now
        self.visibleMonth = now
        self.visibleWeek = now
        self.repository = repository
        self.pageLoader = AgendaPageLoader(repository: repository)
        self.cacheReader = AgendaCacheWindowReader(repository: repository)
        self.officialURL = repository.officialURL
        self.filterStore = filterStore
        self.groupSelection = persisted.selection
        self.featuredGroupKeys = persisted.featuredGroupKeys
        self.knownGroups = agendaMergedGroupNames(
            preferred: persisted.cachedGroups,
            fallback: []
        )
        self.directoryRevision = persisted.directoryRevision
    }

    public var availableGroups: [String] { knownGroups }

    public var featuredGroups: [String] {
        availableGroups.filter { featuredGroupKeys.contains(agendaGroupKey($0)) }
    }

    public var areAllFeaturedGroupsFollowed: Bool {
        !featuredGroups.isEmpty && featuredGroups.allSatisfy(isFollowing)
    }

    public var isGroupFilterActive: Bool {
        if case .custom = groupSelection { return true }
        return false
    }

    public var selectedGroupCount: Int {
        switch groupSelection {
        case .all:
            availableGroups.count
        case let .custom(keys):
            keys.intersection(Set(availableGroups.map(agendaGroupKey))).count
        }
    }

    public func isFollowing(groupName: String) -> Bool {
        switch groupSelection {
        case .all:
            true
        case let .custom(keys):
            keys.contains(agendaGroupKey(groupName))
        }
    }

    public func setFollowing(_ following: Bool, groupName: String) {
        let key = agendaGroupKey(groupName)
        switch groupSelection {
        case .all:
            guard !following else { return }
            var keys = Set(availableGroups.map(agendaGroupKey))
            keys.remove(key)
            groupSelection = .custom(keys)
        case let .custom(currentKeys):
            var keys = currentKeys
            if following { keys.insert(key) } else { keys.remove(key) }
            groupSelection = .custom(keys)
        }
        filterDidChange()
    }

    public func followAllGroups() {
        guard isGroupFilterActive else { return }
        groupSelection = .all
        filterDidChange()
    }

    public func toggleFollowingAllGroups() {
        groupSelection = isGroupFilterActive ? .all : .custom([])
        filterDidChange()
    }

    public func toggleFollowingFeaturedGroups() {
        let keys = Set(featuredGroups.map(agendaGroupKey))
        guard !keys.isEmpty else { return }
        switch groupSelection {
        case .all:
            groupSelection = .custom(Set(availableGroups.map(agendaGroupKey)).subtracting(keys))
        case let .custom(currentKeys):
            groupSelection = .custom(
                areAllFeaturedGroupsFollowed
                    ? currentKeys.subtracting(keys)
                    : currentKeys.union(keys)
            )
        }
        filterDidChange()
    }

    public func isFeatured(groupName: String) -> Bool {
        featuredGroupKeys.contains(agendaGroupKey(groupName))
    }

    public func setFeatured(_ featured: Bool, groupName: String) {
        let key = agendaGroupKey(groupName)
        if featured { featuredGroupKeys.insert(key) } else { featuredGroupKeys.remove(key) }
        persistFilterState()
    }

    public func loadGroupDirectory(forceRefresh: Bool = false) async {
        groupDirectoryErrorMessage = nil
        do {
            let directory = try await repository.groupDirectory(forceRefresh: forceRefresh)
            knownGroups = agendaMergedGroupNames(
                preferred: directory.groups,
                fallback: knownGroups + eventWindow.participatingGroupNames
            )
            if !directory.revision.isEmpty { directoryRevision = directory.revision }
            persistFilterState()
        } catch {
            groupDirectoryErrorMessage = error.localizedDescription
        }
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

    private func updateVisibleMonthEvents() {
        let dayEvents = eventWindow.events(on: selectedDate)
        events = dayEvents.filter(matchesGroupSelection)
        otherEvents = dayEvents.filter { !matchesGroupSelection($0) }
        eventDateKeys = eventWindow.dateKeys(matching: matchesGroupSelection)
        monthEvents = eventWindow.events(inMonthContaining: visibleMonth)
            .filter(matchesGroupSelection)
    }

    private func matchesGroupSelection(_ event: CastellEvent) -> Bool {
        switch groupSelection {
        case .all:
            true
        case let .custom(keys):
            event.participatingGroups.contains { keys.contains(agendaGroupKey($0)) }
        }
    }

    private func filterDidChange() {
        updateVisibleMonthEvents()
        persistFilterState()
    }

    private func mergeObservedGroups() {
        knownGroups = agendaMergedGroupNames(
            preferred: knownGroups,
            fallback: eventWindow.participatingGroupNames
        )
        persistFilterState()
    }

    private func persistFilterState() {
        filterStore?.save(
            AgendaFilterState(
                selection: groupSelection,
                featuredGroupKeys: featuredGroupKeys,
                cachedGroups: knownGroups,
                directoryRevision: directoryRevision
            )
        )
    }
}
