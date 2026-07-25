import Foundation
import Observation

@MainActor
@Observable
final class StartupLoadingGate {
    static let minimumDuration = Duration.milliseconds(250)
    static let maximumDuration = Duration.seconds(2)

    private(set) var hasMetMinimumDuration = false
    private(set) var hasReachedMaximumDuration = false

    func shouldPresent(initialLoadHasCompleted: Bool) -> Bool {
        guard !hasReachedMaximumDuration else { return false }
        return !hasMetMinimumDuration || !initialLoadHasCompleted
    }

    func waitForMinimumDuration() async {
        guard !hasMetMinimumDuration else { return }
        do {
            try await Task.sleep(for: Self.minimumDuration)
        } catch {
            return
        }
        hasMetMinimumDuration = true
    }

    func waitForMaximumDuration() async {
        guard !hasReachedMaximumDuration else { return }
        do {
            try await Task.sleep(for: Self.maximumDuration)
        } catch {
            return
        }
        hasReachedMaximumDuration = true
    }
}
