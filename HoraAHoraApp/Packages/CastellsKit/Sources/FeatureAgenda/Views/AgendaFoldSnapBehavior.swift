import SwiftUI

/// Snaps the scroll resting position out of the fold zone: releasing at half
/// the fold travel or more settles collapsed, below it settles expanded.
struct AgendaFoldSnapBehavior: ScrollTargetBehavior {
    let foldDistance: CGFloat

    func updateTarget(_ target: inout ScrollTarget, context: TargetContext) {
        target.rect.origin.y = AgendaCalendarFold.snapTargetOffset(
            proposedOffset: target.rect.origin.y,
            foldDistance: foldDistance
        )
    }
}
