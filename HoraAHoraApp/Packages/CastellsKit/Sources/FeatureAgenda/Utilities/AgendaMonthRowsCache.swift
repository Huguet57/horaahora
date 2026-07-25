import Foundation

/// Month grids are immutable. Keeping a small, locked value cache avoids
/// rebuilding three 35–42-day matrices for every frame of the fold animation.
final class AgendaMonthRowsCache: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [Date: [[Date]]] = [:]

    func rows(for monthStart: Date) -> [[Date]]? {
        lock.lock()
        defer { lock.unlock() }
        return storage[monthStart]
    }

    func insert(_ rows: [[Date]], for monthStart: Date) {
        lock.lock()
        defer { lock.unlock() }
        if storage.count >= 36 {
            storage.removeAll(keepingCapacity: true)
        }
        storage[monthStart] = rows
    }
}
