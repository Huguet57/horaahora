import SwiftUI

struct StartupLoadingContainer<Content: View>: View {
    let initialLoadHasCompleted: Bool

    @State private var gate = StartupLoadingGate()
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private let content: Content

    init(
        initialLoadHasCompleted: Bool,
        @ViewBuilder content: () -> Content
    ) {
        self.initialLoadHasCompleted = initialLoadHasCompleted
        self.content = content()
    }

    var body: some View {
        ZStack {
            content
                .accessibilityHidden(isLoadingScreenPresented)

            if isLoadingScreenPresented {
                StartupLoadingView()
                    .transition(.opacity)
                    .zIndex(1)
            }
        }
        .animation(
            reduceMotion ? nil : .easeOut(duration: 0.25),
            value: isLoadingScreenPresented
        )
        .task { await gate.waitForMinimumDuration() }
        .task { await gate.waitForMaximumDuration() }
    }

    private var isLoadingScreenPresented: Bool {
        gate.shouldPresent(initialLoadHasCompleted: initialLoadHasCompleted)
    }
}
