import SwiftUI

extension View {
    @ViewBuilder
    func agendaNavigationBarHidden() -> some View {
        #if os(iOS)
        toolbar(.hidden, for: .navigationBar)
        #else
        self
        #endif
    }
}
