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

extension View {
    /// Opens the link, while there is one, in an in-app browser over the whole screen.
    func inAppBrowser(for link: Binding<PresentedLink?>) -> some View {
        sheet(item: link) { link in
            InAppBrowser(url: link.url)
                .ignoresSafeArea()
        }
    }
}

/// The app's tabs, with their titles and icons.
extension View {
    func calculatorTabItem() -> some View {
        tabItem { Label("Calculadora", systemImage: "plus.forwardslash.minus") }
    }

    func comparatorTabItem() -> some View {
        tabItem { Label("Comparador", systemImage: "tablecells") }
    }

    func scoreTableTabItem() -> some View {
        tabItem { Label("Puntuacions", systemImage: "list.number") }
    }

    func settingsTabItem() -> some View {
        tabItem { Label("Ajustos", systemImage: "gearshape") }
    }
}
