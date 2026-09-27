import SwiftUI

struct StartupLoadingContainer<Content: View>: View {
    @State private var gate = StartupLoadingGate()
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private let content: Content

    init(@ViewBuilder content: () -> Content) {
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
    }

    private var isLoadingScreenPresented: Bool {
        !gate.hasMetMinimumDuration
    }
}
