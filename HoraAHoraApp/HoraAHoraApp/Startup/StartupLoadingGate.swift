import Foundation
import Observation

/// Keeps the brand on screen for a moment at launch, so it never just flashes.
@MainActor
@Observable
final class StartupLoadingGate {
    static let minimumDuration = Duration.milliseconds(250)

    private(set) var hasMetMinimumDuration = false

    func waitForMinimumDuration() async {
        guard !hasMetMinimumDuration else { return }
        do {
            try await Task.sleep(for: Self.minimumDuration)
        } catch {
            return
        }
        hasMetMinimumDuration = true
    }
}
