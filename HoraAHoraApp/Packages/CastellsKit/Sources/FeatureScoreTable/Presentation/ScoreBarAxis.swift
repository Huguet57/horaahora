import CoreGraphics
import Foundation

/// The points a bar spans, following the part of the table on screen.
///
/// The smallest value on screen keeps `leadingFraction` of the bar and the largest fills it,
/// so that neighbouring castells differ visibly. A castell leaving or entering the screen
/// counts in proportion to its weight, so the scale moves smoothly while scrolling.
struct ScoreBarAxis: Equatable {
    static let leadingFraction = 0.06
    /// Castells weighing at least this count as whole; the rest only pull the scale partway.
    private static let wholeRow = 0.999

    let lowerBound: Double
    let upperBound: Double

    /// The whole table, until the screen reports which rows show.
    init(castells: [ScoreTableCastell]) {
        self.init(
            lowest: Double(castells.map(\.lowestPoints).min() ?? 0),
            highest: Double(castells.map(\.highestPoints).max() ?? 0)
        )
    }

    init?(visible: [(castell: ScoreTableCastell, fraction: Double)]) {
        let shown = visible.filter { $0.fraction > 0 }
        guard !shown.isEmpty else { return nil }
        let whole = shown.filter { $0.fraction >= Self.wholeRow }
        let anchors = whole.isEmpty ? shown : whole
        let baseHighest = Double(anchors.map(\.castell.highestPoints).max() ?? 0)
        let baseLowest = Double(anchors.map(\.castell.lowestPoints).min() ?? 0)
        var highest = baseHighest
        var lowest = baseLowest
        if !whole.isEmpty {
            for (castell, fraction) in shown where fraction < Self.wholeRow {
                highest = max(highest, baseHighest + (Double(castell.highestPoints) - baseHighest) * fraction)
                lowest = min(lowest, baseLowest + (Double(castell.lowestPoints) - baseLowest) * fraction)
            }
        }
        self.init(lowest: lowest, highest: highest)
    }

    private init(lowest: Double, highest: Double) {
        let span = max(highest - lowest, 1)
        lowerBound = lowest - span * Self.leadingFraction / (1 - Self.leadingFraction)
        upperBound = highest
    }

    /// How much of the bar `points` fill, between 0 and 1.
    func fraction(of points: Int) -> Double {
        let span = upperBound - lowerBound
        guard span > 0 else { return 1 }
        return min(max((Double(points) - lowerBound) / span, 0), 1)
    }

    /// How much a castell counts in the scale, from where its bar is on screen. A bar in the
    /// window counts whole, so it never overflows; outside it counts less and less over
    /// `fadeAbove` or `fadeBelow` points, while it passes under the group header or the tab bar.
    static func weight(
        ofBarAt y: CGFloat,
        in window: ClosedRange<CGFloat>,
        fadeAbove: CGFloat,
        fadeBelow: CGFloat
    ) -> Double {
        if window.contains(y) { return 1 }
        let distance = y < window.lowerBound ? window.lowerBound - y : y - window.upperBound
        let fade = y < window.lowerBound ? fadeAbove : fadeBelow
        guard fade > 0 else { return 0 }
        return Double(max(1 - distance / fade, 0))
    }
}

private extension ScoreTableCastell {
    var highestPoints: Int { max(loaded, unloaded) }
    var lowestPoints: Int { min(loaded, unloaded) }
}
