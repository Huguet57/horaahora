import SafariServices
import SwiftUI
import CastellsDomain
import FeatureAgenda
import FeatureCalculator
import FeatureHourByHour

struct ContentView: View {
    let dependencies: AppDependencies

    @State private var selectedSection = AppSection.hourByHour
    @State private var presentedLink: PresentedLink?

    var body: some View {
        TabView(selection: $selectedSection) {
            HourByHourRootView(repository: dependencies.hourByHourRepository) { url in
                presentedLink = PresentedLink(url: url)
            }
            .tabItem { Label("Hora a Hora", systemImage: "clock") }
            .tag(AppSection.hourByHour)

            AgendaRootView(repository: dependencies.agendaRepository)
                .tabItem { Label("Agenda", systemImage: "calendar") }
                .tag(AppSection.agenda)

            CalculatorRootView(repository: dependencies.chatRepository)
                .tabItem { Label("Calculadora", systemImage: "rectangle.grid.3x2.fill") }
                .tag(AppSection.calculator)
        }
        .onAppear {
            if let pendingURL = AppDelegate.shared?.consumePendingDeepLinkURL() {
                openHourByHourLink(pendingURL)
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .hourByHourDeepLink)) { notification in
            guard let url = notification.userInfo?[AppDelegate.deepLinkURLKey] as? URL else { return }
            _ = AppDelegate.shared?.consumePendingDeepLinkURL()
            openHourByHourLink(url)
        }
        .sheet(item: $presentedLink) { link in
            InAppBrowser(url: link.url)
                .ignoresSafeArea()
        }
    }

    private func openHourByHourLink(_ url: URL) {
        selectedSection = .hourByHour
        presentedLink = PresentedLink(url: url)
    }
}

private enum AppSection: Hashable {
    case hourByHour
    case agenda
    case calculator
}

private struct PresentedLink: Identifiable {
    let id = UUID()
    let url: URL
}

private struct InAppBrowser: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ viewController: SFSafariViewController, context: Context) {}
}
