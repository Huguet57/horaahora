import Foundation
import Observation
import CastellsDomain

@MainActor
@Observable
public final class HourByHourViewModel {
    typealias Sleep = @MainActor @Sendable (Duration) async throws -> Void

    private static let minimumRefreshDuration = Duration.milliseconds(500)

    public private(set) var items: [HourByHourItem] = []
    public private(set) var dayGroups: [HourByHourDayGroup] = []
    public private(set) var newItemsRevision = 0
    public private(set) var isLoading = false
    public private(set) var isLoadingMore = false
    public private(set) var hasCompletedInitialLoad = false
    public private(set) var isFromCache = false
    public private(set) var errorMessage: String?
    private var nextCursor: String?
    private let repository: any HourByHourRepository
    private let sleep: Sleep

    public convenience init(repository: any HourByHourRepository) {
        self.init(
            repository: repository,
            sleep: { duration in try await ContinuousClock().sleep(for: duration) }
        )
    }

    init(repository: any HourByHourRepository, sleep: @escaping Sleep) {
        self.repository = repository
        self.sleep = sleep
    }

    public func loadIfNeeded() async {
        guard items.isEmpty, !isLoading else { return }
        await load(forceRefresh: false)
        guard !Task.isCancelled else { return }
        hasCompletedInitialLoad = true
    }

    public func refresh() async {
        let clock = ContinuousClock()
        let startedAt = clock.now
        await load(forceRefresh: true, mergePolicy: .replace)
        try? await clock.sleep(until: startedAt.advanced(by: Self.minimumRefreshDuration))
    }

    public func revalidate() async {
        await load(forceRefresh: false, mergePolicy: .revalidate)
    }

    public func runAutoRefresh(every interval: Duration = .seconds(60)) async {
        if items.isEmpty {
            await loadIfNeeded()
        } else {
            await revalidate()
        }
        while !Task.isCancelled {
            do {
                try await sleep(interval)
            } catch {
                return
            }
            guard !Task.isCancelled else { return }
            await revalidate()
        }
    }

    public func loadNextIfNeeded(after item: HourByHourItem) async {
        guard
            item.id == items.last?.id,
            nextCursor != nil,
            !isLoading,
            !isLoadingMore
        else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        do {
            let page = try await repository.page(
                cursor: nextCursor,
                limit: 30,
                forceRefresh: false
            )
            merge(page.items, policy: .append)
            nextCursor = page.nextCursor
            isFromCache = page.fromCache
        } catch {
            guard !Task.isCancelled else { return }
            errorMessage = error.localizedDescription
        }
    }

    private func load(
        forceRefresh: Bool,
        mergePolicy: HourByHourItemMerger.Policy = .replace
    ) async {
        guard !isLoading, !isLoadingMore else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let page = try await repository.page(
                cursor: nil,
                limit: 30,
                forceRefresh: forceRefresh
            )
            let shouldAdoptFreshCursor = nextCursor == nil
            merge(page.items, policy: mergePolicy)
            if mergePolicy == .replace || shouldAdoptFreshCursor {
                nextCursor = page.nextCursor
            }
            isFromCache = page.fromCache
        } catch {
            guard !Task.isCancelled else { return }
            errorMessage = error.localizedDescription
        }
    }

    private func merge(_ incoming: [HourByHourItem], policy: HourByHourItemMerger.Policy) {
        let result = HourByHourItemMerger.merge(incoming, into: items, policy: policy)
        guard result.items != items else { return }
        items = result.items
        dayGroups = HourByHourDayGrouping.groups(from: result.items)
        if result.containsNewItems {
            newItemsRevision &+= 1
        }
    }
}
