import Foundation
import Observation
import SwiftUI
import CastellsDomain

enum AgendaCalendarMath {
    static var calendar: Calendar {
        var value = Calendar(identifier: .gregorian)
        value.locale = Locale(identifier: "ca_ES")
        value.timeZone = TimeZone(identifier: "Europe/Madrid")!
        value.firstWeekday = 2
        return value
    }

    static func week(containing date: Date) -> [Date] {
        let startOfDay = calendar.startOfDay(for: date)
        let weekday = calendar.component(.weekday, from: startOfDay)
        let daysSinceMonday = (weekday - calendar.firstWeekday + 7) % 7
        guard let monday = calendar.date(byAdding: .day, value: -daysSinceMonday, to: startOfDay) else {
            return []
        }
        return (0..<7).compactMap { calendar.date(byAdding: .day, value: $0, to: monday) }
    }

    static func prefetchRanges(containing date: Date) -> [(start: Date, end: Date)] {
        guard
            let monthInterval = calendar.dateInterval(of: .month, for: date),
            let windowStart = calendar.date(byAdding: .month, value: -6, to: monthInterval.start),
            let currentMonthEnd = calendar.date(byAdding: .day, value: -1, to: monthInterval.end),
            let windowEndExclusive = calendar.date(byAdding: .month, value: 6, to: monthInterval.end),
            let windowEnd = calendar.date(byAdding: .day, value: -1, to: windowEndExclusive)
        else { return [] }

        return [
            (windowStart, currentMonthEnd),
            (monthInterval.end, windowEnd)
        ]
    }

    static func monthRange(containing date: Date) -> (start: Date, end: Date)? {
        guard
            let interval = calendar.dateInterval(of: .month, for: date),
            let end = calendar.date(byAdding: .day, value: -1, to: interval.end)
        else { return nil }

        return (interval.start, end)
    }

    static func localDateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    static func monthKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "yyyy-MM"
        return formatter.string(from: date)
    }

    static func monthStarts(from start: Date, through end: Date) -> [Date] {
        guard var month = calendar.dateInterval(of: .month, for: start)?.start else { return [] }
        var result: [Date] = []
        while month <= end {
            result.append(month)
            guard let next = calendar.date(byAdding: .month, value: 1, to: month) else { break }
            month = next
        }
        return result
    }
}

@MainActor
@Observable
public final class AgendaViewModel {
    public var selectedDate: Date
    public private(set) var visibleMonth: Date
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
        }
        let ranges = AgendaCalendarMath.prefetchRanges(containing: visibleMonth)
        _ = restoreCachedSnapshot(in: ranges)
    }

    public func select(_ date: Date) {
        selectedDate = date
        visibleMonth = date
        updateVisibleMonthEvents()
    }

    public func selectAndLoad(_ date: Date) async {
        select(date)
        await extendPrefetchWindowIfNeeded()
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
        await extendPrefetchWindowIfNeeded()
    }

    public func changeWeek(by offset: Int) async {
        guard let date = AgendaCalendarMath.calendar.date(
            byAdding: .day,
            value: offset * 7,
            to: selectedDate
        ) else {
            return
        }
        await selectAndLoad(date)
    }

    public func load(forceRefresh: Bool = false) async {
        errorMessage = nil
        if !hasStartedInitialLoad {
            visibleMonth = selectedDate
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

    private func extendPrefetchWindowIfNeeded() async {
        let desiredRanges = AgendaCalendarMath.prefetchRanges(containing: visibleMonth)
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

public struct AgendaRootView: View {
    private let model: AgendaViewModel
    @State private var isCalendarExpanded = true
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    public init(model: AgendaViewModel) {
        self.model = model
    }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                AgendaCalendarView(
                    selectedDate: model.selectedDate,
                    visibleMonth: model.visibleMonth,
                    eventDateKeys: model.eventDateKeys,
                    isExpanded: isCalendarExpanded,
                    onToggle: {
                        setCalendarExpanded(!isCalendarExpanded)
                    },
                    onSelect: { date in
                        Task { await model.selectAndLoad(date) }
                    },
                    onChangeWeek: { offset in
                        Task { await model.changeWeek(by: offset) }
                    },
                    onChangeMonth: { offset in
                        Task { await model.changeMonth(by: offset) }
                    }
                )
                .padding(.horizontal)
                .padding(.top, 8)
                .padding(.bottom, 12)

                Divider()

                ScrollView {
                    if model.isLoading && model.events.isEmpty {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else if !model.events.isEmpty {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(model.events) { event in
                                AgendaEventCard(event: event)
                            }
                        }
                    } else if model.errorMessage != nil {
                        OfficialAgendaFallback(
                            officialURL: model.officialURL,
                            message: "No s'ha pogut connectar al servidor."
                        ) {
                            Task { await model.load(forceRefresh: true) }
                        }
                    } else if model.sourceStatus == .unavailable {
                        OfficialAgendaFallback(
                            officialURL: model.officialURL,
                            message: "Les dades natives no estan disponibles ara mateix."
                        ) {
                            Task { await model.load(forceRefresh: true) }
                        }
                    } else {
                        Text("No hi ha actuacions aquest dia")
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 20)
                    }
                }
                .contentMargins(16, for: .scrollContent)
                .refreshable { await model.load(forceRefresh: true) }
            }
            .agendaNavigationBarHidden()
            .task { await model.load() }
        }
    }

    private func setCalendarExpanded(_ expanded: Bool) {
        if reduceMotion {
            isCalendarExpanded = expanded
        } else {
            withAnimation(.snappy(duration: 0.25)) {
                isCalendarExpanded = expanded
            }
        }
    }
}

private extension View {
    @ViewBuilder
    func agendaNavigationBarHidden() -> some View {
        #if os(iOS)
        toolbar(.hidden, for: .navigationBar)
        #else
        self
        #endif
    }
}

private struct OfficialAgendaFallback: View {
    let officialURL: URL
    let message: String
    let retry: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "wifi.exclamationmark")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 24, height: 24)

            VStack(alignment: .leading, spacing: 8) {
                Text("Agenda temporalment no disponible")
                    .font(.subheadline.weight(.semibold))

                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: 16) {
                    Button(action: retry) {
                        Label("Torna-ho a provar", systemImage: "arrow.clockwise")
                    }

                    Link(destination: officialURL) {
                        Label("Agenda oficial", systemImage: "arrow.up.right")
                    }
                }
                .font(.caption.weight(.medium))
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 12))
    }
}

private struct AgendaCalendarView: View {
    let selectedDate: Date
    let visibleMonth: Date
    let eventDateKeys: Set<String>
    let isExpanded: Bool
    let onToggle: () -> Void
    let onSelect: (Date) -> Void
    let onChangeWeek: (Int) -> Void
    let onChangeMonth: (Int) -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var weekDragOffset: CGFloat = 0
    @State private var monthDragOffset: CGFloat = 0
    @State private var monthPageWidth: CGFloat = 1

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: 7)
    private let weekdays = ["DL", "DT", "DC", "DJ", "DV", "DS", "DG"]

    var body: some View {
        VStack(spacing: 14) {
            HStack {
                Button(action: onToggle) {
                    HStack(spacing: 7) {
                        Text(monthTitle)
                            .font(.title3.weight(.semibold))
                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .font(.caption.weight(.bold))
                            .foregroundStyle(.secondary)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(
                    isExpanded ? "Plega el calendari mensual" : "Mostra el calendari mensual"
                )
                .accessibilityValue(isExpanded ? "Desplegat" : "Plegat")
                Spacer()
                Button { changeVisiblePeriod(by: -1) } label: {
                    Image(systemName: "chevron.left")
                        .font(.title2.weight(.semibold))
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel(isExpanded ? "Mes anterior" : "Setmana anterior")
                Button { changeVisiblePeriod(by: 1) } label: {
                    Image(systemName: "chevron.right")
                        .font(.title2.weight(.semibold))
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel(isExpanded ? "Mes següent" : "Setmana següent")
            }
            .contentShape(Rectangle())
            .highPriorityGesture(calendarVerticalDragGesture)

            if isExpanded {
                monthPager
                    .transition(.opacity.combined(with: .move(edge: .top)))
            } else {
                weekPager
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .contentShape(Rectangle())
        .accessibilityAction(named: "Setmana anterior") { onChangeWeek(-1) }
        .accessibilityAction(named: "Setmana següent") { onChangeWeek(1) }
        .onChange(of: selectedDate) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                weekDragOffset = 0
            }
        }
        .onChange(of: visibleMonth) { _, _ in
            var transaction = Transaction()
            transaction.disablesAnimations = true
            withTransaction(transaction) {
                monthDragOffset = 0
            }
        }
    }

    private func changeVisiblePeriod(by offset: Int) {
        if isExpanded {
            onChangeMonth(offset)
        } else {
            onChangeWeek(offset)
        }
    }

    private var calendarVerticalDragGesture: some Gesture {
        DragGesture(minimumDistance: 24)
            .onEnded { value in
                handleVerticalDrag(value.translation)
            }
    }

    private func handleVerticalDrag(_ translation: CGSize) {
        guard
            abs(translation.height) > abs(translation.width),
            abs(translation.height) >= 36
        else {
            return
        }

        if translation.height < 0, isExpanded {
            onToggle()
        } else if translation.height > 0, !isExpanded {
            onToggle()
        }
    }

    private var monthPager: some View {
        GeometryReader { geometry in
            let pageWidth = geometry.size.width
            HStack(alignment: .top, spacing: 0) {
                monthGrid(containing: monthDate(offset: -1))
                    .frame(width: pageWidth)
                monthGrid(containing: visibleMonth)
                    .frame(width: pageWidth)
                monthGrid(containing: monthDate(offset: 1))
                    .frame(width: pageWidth)
            }
            .frame(width: pageWidth * 3, alignment: .leading)
            .offset(x: -pageWidth + monthDragOffset)
            .contentShape(Rectangle())
            .highPriorityGesture(monthPagingGesture(pageWidth: pageWidth))
            .onAppear { monthPageWidth = pageWidth }
            .onChange(of: pageWidth) { _, newWidth in monthPageWidth = newWidth }
        }
        .frame(height: monthPagerHeight)
        .clipped()
    }

    private func monthGrid(containing referenceDate: Date) -> some View {
        LazyVGrid(columns: columns, spacing: 8) {
            weekdayHeaders

            ForEach(0..<leadingBlankCount(containing: referenceDate), id: \.self) { _ in
                Color.clear.frame(height: 42)
            }

            ForEach(daysInMonth(containing: referenceDate), id: \.self) { date in
                dayButton(date)
            }
        }
    }

    private func monthDate(offset: Int) -> Date {
        calendar.date(byAdding: .month, value: offset, to: visibleMonth) ?? visibleMonth
    }

    private var monthPagerHeight: CGFloat {
        let currentHeight = monthGridHeight(containing: visibleMonth)
        guard monthDragOffset != 0 else { return currentHeight }
        let direction = monthDragOffset < 0 ? 1 : -1
        let targetHeight = monthGridHeight(containing: monthDate(offset: direction))
        let progress = min(abs(monthDragOffset) / max(monthPageWidth, 1), 1)
        return currentHeight + (targetHeight - currentHeight) * progress
    }

    private func monthGridHeight(containing referenceDate: Date) -> CGFloat {
        let cells = leadingBlankCount(containing: referenceDate)
            + daysInMonth(containing: referenceDate).count
        let rows = Int(ceil(Double(cells) / 7.0))
        return 16 + 8 + CGFloat(rows * 44) + CGFloat(max(0, rows - 1) * 8)
    }

    private func monthPagingGesture(pageWidth: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    return
                }
                monthDragOffset = value.translation.width
            }
            .onEnded { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    animateMonthDrag(to: 0)
                    handleVerticalDrag(value.translation)
                    return
                }

                let predictedDistance = value.predictedEndTranslation.width
                let shouldChangeMonth = abs(value.translation.width) > pageWidth * 0.2
                    || abs(predictedDistance) > pageWidth * 0.45
                guard shouldChangeMonth else {
                    animateMonthDrag(to: 0)
                    return
                }

                let direction = value.translation.width < 0 ? 1 : -1
                let targetOffset = direction > 0 ? -pageWidth : pageWidth
                completeMonthDrag(to: targetOffset, direction: direction)
            }
    }

    private func animateMonthDrag(to offset: CGFloat) {
        if reduceMotion {
            monthDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                monthDragOffset = offset
            }
        }
    }

    private func completeMonthDrag(to offset: CGFloat, direction: Int) {
        if reduceMotion {
            monthDragOffset = 0
            onChangeMonth(direction)
        } else {
            withAnimation(.snappy(duration: 0.22), completionCriteria: .logicallyComplete) {
                monthDragOffset = offset
            } completion: {
                onChangeMonth(direction)
            }
        }
    }

    private var weekPager: some View {
        GeometryReader { geometry in
            let pageWidth = geometry.size.width
            HStack(spacing: 0) {
                weekGrid(containing: weekDate(offset: -1))
                    .frame(width: pageWidth)
                weekGrid(containing: selectedDate)
                    .frame(width: pageWidth)
                weekGrid(containing: weekDate(offset: 1))
                    .frame(width: pageWidth)
            }
            .frame(width: pageWidth * 3, alignment: .leading)
            .offset(x: -pageWidth + weekDragOffset)
            .contentShape(Rectangle())
            .highPriorityGesture(weekPagingGesture(pageWidth: pageWidth))
        }
        .frame(height: 68)
        .clipped()
    }

    private func weekGrid(containing referenceDate: Date) -> some View {
        LazyVGrid(columns: columns, spacing: 4) {
            weekdayHeaders

            ForEach(AgendaCalendarMath.week(containing: referenceDate), id: \.self) { date in
                dayButton(date)
            }
        }
    }

    private func weekDate(offset: Int) -> Date {
        calendar.date(byAdding: .day, value: offset * 7, to: selectedDate) ?? selectedDate
    }

    private func weekPagingGesture(pageWidth: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    return
                }
                weekDragOffset = value.translation.width
            }
            .onEnded { value in
                guard abs(value.translation.width) > abs(value.translation.height) else {
                    animateWeekDrag(to: 0)
                    handleVerticalDrag(value.translation)
                    return
                }

                let predictedDistance = value.predictedEndTranslation.width
                let shouldChangeWeek = abs(value.translation.width) > pageWidth * 0.2
                    || abs(predictedDistance) > pageWidth * 0.45
                guard shouldChangeWeek else {
                    animateWeekDrag(to: 0)
                    return
                }

                let direction = value.translation.width < 0 ? 1 : -1
                let targetOffset = direction > 0 ? -pageWidth : pageWidth
                completeWeekDrag(to: targetOffset, direction: direction)
            }
    }

    private func animateWeekDrag(to offset: CGFloat) {
        if reduceMotion {
            weekDragOffset = offset
        } else {
            withAnimation(.snappy(duration: 0.22)) {
                weekDragOffset = offset
            }
        }
    }

    private func completeWeekDrag(to offset: CGFloat, direction: Int) {
        if reduceMotion {
            weekDragOffset = 0
            onChangeWeek(direction)
        } else {
            withAnimation(.snappy(duration: 0.22), completionCriteria: .logicallyComplete) {
                weekDragOffset = offset
            } completion: {
                onChangeWeek(direction)
            }
        }
    }

    @ViewBuilder
    private var weekdayHeaders: some View {
        ForEach(weekdays, id: \.self) { weekday in
            Text(weekday)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.tertiary)
        }
    }

    private func dayButton(_ date: Date) -> some View {
        let selected = calendar.isDate(date, inSameDayAs: selectedDate)
        let today = calendar.isDateInToday(date)
        let isPast = calendar.compare(date, to: Date(), toGranularity: .day) == .orderedAscending
        let hasEvents = eventDateKeys.contains(localDateKey(date))
        return Button { onSelect(date) } label: {
            ZStack {
                Circle()
                    .fill(selected ? Color.accentColor : .clear)
                    .frame(width: 42, height: 42)
                VStack(spacing: 1) {
                    Text(String(calendar.component(.day, from: date)))
                        .font(.body.monospacedDigit())
                        .foregroundStyle(selected ? Color.white : today ? Color.accentColor : Color.primary)
                    Circle()
                        .fill(hasEvents ? (selected ? Color.white : Color.accentColor) : .clear)
                        .frame(width: 5, height: 5)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44)
        }
        .buttonStyle(.plain)
        .opacity(isPast && !selected ? 0.35 : 1)
        .accessibilityLabel(accessibilityDate(date))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityHint(hasEvents ? "Té actuacions" : "")
    }

    private var calendar: Calendar {
        AgendaCalendarMath.calendar
    }

    private var monthStart: Date {
        monthStart(containing: isExpanded ? visibleMonth : selectedDate)
    }

    private func monthStart(containing date: Date) -> Date {
        calendar.dateInterval(of: .month, for: date)!.start
    }

    private func leadingBlankCount(containing date: Date) -> Int {
        (calendar.component(.weekday, from: monthStart(containing: date)) + 5) % 7
    }

    private func daysInMonth(containing date: Date) -> [Date] {
        let start = monthStart(containing: date)
        let count = calendar.range(of: .day, in: .month, for: start)?.count ?? 0
        return (0..<count).compactMap { calendar.date(byAdding: .day, value: $0, to: start) }
    }

    private var monthTitle: String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateFormat = "LLLL 'del' yyyy"
        return formatter.string(from: monthStart)
    }

    private func localDateKey(_ date: Date) -> String {
        AgendaCalendarMath.localDateKey(date)
    }

    private func accessibilityDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.locale = Locale(identifier: "ca_ES")
        formatter.timeZone = calendar.timeZone
        formatter.dateStyle = .full
        return formatter.string(from: date)
    }
}

private struct AgendaEventCard: View {
    let event: CastellEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Label(event.timeLabel, systemImage: "clock")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text(event.municipality)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Text(event.title)
                .font(.headline)

            if !event.venue.isEmpty,
               let mapsURL = googleMapsSearchURL(
                   venue: event.venue,
                   municipality: event.municipality
               ) {
                Link(destination: mapsURL) {
                    Label(event.venue, systemImage: "mappin.and.ellipse")
                        .font(.subheadline)
                }
                .accessibilityLabel("Obre \(event.venue) a Google Maps")
            }

            if !event.participatingGroups.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    ForEach(event.participatingGroups, id: \.self) { group in
                        Text("• \(group)")
                    }
                }
                .font(.subheadline)
            }

            if !event.notes.isEmpty {
                Text(event.notes)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Divider()
            HStack {
                Text(event.attribution)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Spacer()
                Link(destination: event.sourceURL) {
                    Image(systemName: "arrow.up.right")
                        .font(.caption)
                }
                .accessibilityLabel("Obre l'agenda oficial")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}

func googleMapsSearchURL(venue: String, municipality: String) -> URL? {
    var components = URLComponents()
    components.scheme = "https"
    components.host = "www.google.com"
    components.path = "/maps/search/"
    components.queryItems = [
        URLQueryItem(name: "api", value: "1"),
        URLQueryItem(name: "query", value: "\(venue), \(municipality)"),
    ]
    return components.url
}
