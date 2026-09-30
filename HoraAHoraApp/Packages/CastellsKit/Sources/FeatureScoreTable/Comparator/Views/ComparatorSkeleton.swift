#if os(iOS)
import SwiftUI

/// How long a fresh copy of a scenario shows as a placeholder before it reveals itself.
let duplicateSkeletonDuration: Duration = .milliseconds(600)

extension View {
    /// Shows the view as a pulsing placeholder while `isActive`, keeping its layout, so that a
    /// copy that looks just like its original reads as a new scenario.
    func duplicateSkeleton(_ isActive: Bool) -> some View {
        modifier(DuplicateSkeleton(isActive: isActive))
    }
}

private struct DuplicateSkeleton: ViewModifier {
    let isActive: Bool
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isPulsing = false

    func body(content: Content) -> some View {
        content
            .redacted(reason: isActive ? .placeholder : [])
            .opacity(opacity)
            .allowsHitTesting(!isActive)
            .onChange(of: isActive, initial: true) { _, isActive in
                guard isActive, !reduceMotion else {
                    isPulsing = false
                    return
                }
                withAnimation(.easeInOut(duration: 0.3).repeatForever(autoreverses: true)) {
                    isPulsing = true
                }
            }
    }

    private var opacity: Double {
        guard isActive else { return 1 }
        guard !reduceMotion else { return 0.68 }
        return isPulsing ? 0.45 : 0.78
    }
}
#endif
