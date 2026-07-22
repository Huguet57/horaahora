import SafariServices
import SwiftUI
import CastellsDomain
import FeatureAgenda
import FeatureCalculator
import FeatureHourByHour
import FeatureSettings

struct ContentView: View {
    let dependencies: AppDependencies

    @State private var hourByHourModel: HourByHourViewModel
    @State private var agendaModel: AgendaViewModel
    @State private var selectedSection = AppSection.hourByHour
    @State private var presentedLink: PresentedLink?
    @State private var settingsModel: SettingsModel
    @Environment(\.openURL) private var openURL
    @Environment(\.scenePhase) private var scenePhase

    init(dependencies: AppDependencies) {
        self.dependencies = dependencies
        _hourByHourModel = State(
            initialValue: HourByHourViewModel(repository: dependencies.hourByHourRepository)
        )
        _agendaModel = State(
            initialValue: AgendaViewModel(repository: dependencies.agendaRepository)
        )
        _settingsModel = State(initialValue: dependencies.settingsModel)
    }

    var body: some View {
        TabView(selection: $selectedSection) {
            HourByHourRootView(
                model: hourByHourModel,
                showsNotificationOnboarding: settingsModel.showsNotificationOnboarding,
                onConfigureNotifications: {
                    settingsModel.handleNotificationOnboarding(.configure) {
                        Task { @MainActor in
                            await Task.yield()
                            selectedSection = .settings
                        }
                    }
                },
                onDismissNotificationOnboarding: {
                    settingsModel.handleNotificationOnboarding(.dismiss)
                }
            ) { url in
                presentedLink = PresentedLink(url: url)
            }
            .tabItem { Label("Hora a Hora", systemImage: "clock") }
            .tag(AppSection.hourByHour)

            AgendaRootView(model: agendaModel)
                .tabItem { Label("Agenda", systemImage: "calendar") }
                .tag(AppSection.agenda)

            CalculatorRootView(repository: dependencies.chatRepository)
                .tabItem { Label("Calculadora", systemImage: "plus.forwardslash.minus") }
                .tag(AppSection.calculator)

            SettingsRootView(
                model: settingsModel,
                configuration: dependencies.settingsConfiguration,
                onOpenURL: { url in
                    presentedLink = PresentedLink(url: url)
                },
                onContactSupport: { url in
                    openURL(url)
                },
                onCopyIdentifier: { identifier in
                    UIPasteboard.general.string = identifier
                }
            )
            .tabItem { Label("Ajustos", systemImage: "gearshape") }
            .tag(AppSection.settings)
        }
        .task {
            agendaModel.preloadFromCache()
            await settingsModel.refreshNotificationStatus()
        }
        .task(id: scenePhase) {
            guard scenePhase == .active else { return }
            await hourByHourModel.runAutoRefresh(every: .seconds(60))
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
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active else { return }
            Task { await settingsModel.refreshNotificationStatus() }
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
    case settings
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
