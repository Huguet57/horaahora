import SafariServices
import SwiftUI

struct PresentedLink: Identifiable {
    let id = UUID()
    let url: URL
}

struct InAppBrowser: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ viewController: SFSafariViewController, context: Context) {}
}

/// The tabs both apps share, with the same titles and icons.
extension View {
    func calculatorTabItem() -> some View {
        tabItem { Label("Calculadora", systemImage: "plus.forwardslash.minus") }
    }

    func scoreTableTabItem() -> some View {
        tabItem { Label("Puntuacions", systemImage: "list.number") }
    }

    func settingsTabItem() -> some View {
        tabItem { Label("Ajustos", systemImage: "gearshape") }
    }
}
