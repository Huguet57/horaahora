import CoreGraphics
import Observation

/// Where each bar of the table is on screen, and the scale that follows from it.
@MainActor
@Observable
final class ScoreBarScale {
    /// How far below the window a bar keeps pulling the scale, under the tab bar.
    private static let fadeBelow: CGFloat = 40

    private(set) var axis: ScoreBarAxis
    /// The castells whose bars show. Bars that scrolled past the window would overflow it, so
    /// they hide instead of showing through the navigation bar.
    private(set) var castellsInWindow: Set<String> = []

    @ObservationIgnored private let castells: [String: ScoreTableCastell]
    @ObservationIgnored private var barFrames: [String: CGRect] = [:]
    @ObservationIgnored private var viewport: CGRect = .null
    @ObservationIgnored private var pinnedHeaderHeight: CGFloat = 0

    init(table: ScoreTable) {
        axis = ScoreBarAxis(castells: table.castells)
        castells = Dictionary(uniqueKeysWithValues: table.castells.map { ($0.notation, $0) })
    }

    /// The part of the screen where the table shows, in global coordinates.
    func setViewport(_ frame: CGRect) {
        viewport = frame
        update()
    }

    /// The group header pinned at the top hides the bars under it.
    func setPinnedHeaderHeight(_ height: CGFloat) {
        pinnedHeaderHeight = height
        update()
    }

    /// A bar's frame in global coordinates, or `nil` once its row leaves the screen.
    func setBarFrame(_ frame: CGRect?, of notation: String) {
        barFrames[notation] = frame
        update()
    }

    private func update() {
        guard !viewport.isNull else { return }
        let top = min(viewport.minY + pinnedHeaderHeight, viewport.maxY)
        let window = top...viewport.maxY
        let weighted = barFrames.compactMap { notation, frame in
            castells[notation].map {
                (
                    castell: $0,
                    fraction: ScoreBarAxis.weight(
                        ofBarAt: frame.midY,
                        in: window,
                        fadeAbove: pinnedHeaderHeight,
                        fadeBelow: Self.fadeBelow
                    )
                )
            }
        }
        if let axis = ScoreBarAxis(visible: weighted), axis != self.axis {
            self.axis = axis
        }
        let inWindow = Set(weighted.filter { $0.fraction > 0 }.map(\.castell.notation))
        if inWindow != castellsInWindow {
            castellsInWindow = inWindow
        }
    }
}
