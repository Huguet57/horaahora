import SwiftUI

extension View {
    func hourByHourNewItemTransition(reduceMotion: Bool) -> some View {
        transition(HourByHourNewItemsMotion.transition(reduceMotion: reduceMotion))
    }

    func hourByHourNewItemsAnimation(revision: Int, reduceMotion: Bool) -> some View {
        animation(
            HourByHourNewItemsMotion.animation(reduceMotion: reduceMotion),
            value: revision
        )
    }
}

private enum HourByHourNewItemsMotion {
    static func transition(reduceMotion: Bool) -> AnyTransition {
        guard !reduceMotion else { return .identity }
        return .asymmetric(
            insertion: .opacity.combined(with: .offset(y: -8)),
            removal: .opacity
        )
    }

    static func animation(reduceMotion: Bool) -> Animation? {
        reduceMotion ? nil : .snappy(duration: 0.32)
    }
}
