import SwiftUI
#if os(iOS)
import UIKit
#elseif os(macOS)
import AppKit
#endif

#if os(iOS)
let agendaGroupFilterBackground = Color(uiColor: .systemGroupedBackground)
#else
let agendaGroupFilterBackground = Color(nsColor: .windowBackgroundColor)
#endif

extension View {
    @ViewBuilder
    func agendaInlineNavigationTitle() -> some View {
#if os(iOS)
        navigationBarTitleDisplayMode(.inline)
#else
        self
#endif
    }

    @ViewBuilder
    func agendaGroupSearch(text: Binding<String>) -> some View {
#if os(iOS)
        searchable(
            text: text,
            placement: .navigationBarDrawer(displayMode: .always),
            prompt: "Cerca una colla"
        )
#else
        searchable(text: text, prompt: "Cerca una colla")
#endif
    }

    @ViewBuilder
    func agendaOpaqueNavigationBar(background: Color) -> some View {
#if os(iOS)
        toolbarBackground(background, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
#else
        self
#endif
    }
}
