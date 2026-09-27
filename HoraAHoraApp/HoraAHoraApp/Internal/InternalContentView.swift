import SwiftUI
import UIKit
import FeatureAgenda
import FeatureCalculator
import FeatureHourByHour
import FeatureInternalSettings
import FeatureScoreTable

enum InternalSection: Hashable {
    case calculator
    case scoreTable
    /// Hidden unless the secret gesture in Ajustos shows it, like `agenda`.
    case hourByHour
    case agenda
    case settings
}

struct InternalContentView: View {
    let dependencies: InternalAppDependencies

    @State private var hourByHourModel: HourByHourViewModel
    @State private var agendaModel: AgendaViewModel
    @State private var selectedSection = InternalSection.calculator
    @State private var showsAgendaGroupFilter = false
    @State private var presentedLink: PresentedLink?
    @State private var internalSettings: InternalSettingsModel
    @Environment(\.openURL) private var openURL
    @Environment(\.scenePhase) private var scenePhase

    init(dependencies: InternalAppDependencies) {
        self.dependencies = dependencies
        _hourByHourModel = State(
            initialValue: HourByHourViewModel(repository: dependencies.hourByHourRepository)
        )
        _agendaModel = State(
            initialValue: AgendaViewModel(
                repository: dependencies.agendaRepository,
                groupDirectoryRepository: dependencies.groupDirectoryRepository,
                filterStore: dependencies.agendaFilterStore
            )
        )
        _internalSettings = State(initialValue: dependencies.internalSettingsModel)
    }

    var body: some View {
        StartupLoadingContainer {
            tabView
        }
        .task {
            agendaModel.preloadFromCache()
            await internalSettings.refreshNotificationStatus()
        }
        .hourByHourAutoRefresh(
            model: hourByHourModel,
            isEnabled: scenePhase == .active && selectedSection == .hourByHour
        )
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
            Task { await internalSettings.refreshNotificationStatus() }
        }
        .onChange(of: internalSettings.showsHiddenSections) { _, showsHiddenSections in
            guard !showsHiddenSections, selectedSection == .hourByHour || selectedSection == .agenda
            else { return }
            selectedSection = .settings
        }
        .sheet(item: $presentedLink) { link in
            InAppBrowser(url: link.url)
                .ignoresSafeArea()
        }
    }

    private var tabView: some View {
        TabView(selection: $selectedSection) {
            CalculatorRootView(
                repository: dependencies.core.chatRepository,
                sharing: dependencies.core.conversationSharing
            )
                .calculatorTabItem()
                .tag(InternalSection.calculator)

            ScoreTableRootView()
                .scoreTableTabItem()
                .tag(InternalSection.scoreTable)

            if internalSettings.showsHiddenSections {
                hiddenSections
            }

            InternalSettingsRootView(
                model: internalSettings,
                settingsModel: dependencies.core.settingsModel,
                configuration: dependencies.core.settingsConfiguration,
                sources: InternalAppDependencies.sources,
                hasFollowedGroups: agendaModel.isGroupFilterActive && agendaModel.selectedGroupCount > 0,
                onChooseGroups: {
                    selectedSection = .agenda
                    showsAgendaGroupFilter = true
                },
                onOpenURL: { url in presentedLink = PresentedLink(url: url) },
                onContactSupport: { url in openURL(url) },
                onCopyIdentifier: { identifier in UIPasteboard.general.string = identifier }
            )
            .settingsTabItem()
            .tag(InternalSection.settings)
        }
    }

    @ViewBuilder
    private var hiddenSections: some View {
        HourByHourRootView(
            model: hourByHourModel,
            showsNotificationOnboarding: internalSettings.showsNotificationOnboarding,
            onConfigureNotifications: {
                internalSettings.handleNotificationOnboarding(.configure) {
                    Task { @MainActor in
                        await Task.yield()
                        selectedSection = .settings
                    }
                }
            },
            onDismissNotificationOnboarding: {
                internalSettings.handleNotificationOnboarding(.dismiss)
            }
        ) { url in
            presentedLink = PresentedLink(url: url)
        }
        .tabItem { Label("Hora a Hora", systemImage: "clock") }
        .tag(InternalSection.hourByHour)

        AgendaRootView(model: agendaModel, showsGroupFilter: $showsAgendaGroupFilter)
            .tabItem { Label("Agenda", systemImage: "calendar") }
            .tag(InternalSection.agenda)
    }

    /// A tapped news notification opens its page, over Hora a Hora when it is shown.
    private func openHourByHourLink(_ url: URL) {
        if internalSettings.showsHiddenSections {
            selectedSection = .hourByHour
        }
        presentedLink = PresentedLink(url: url)
    }
}
