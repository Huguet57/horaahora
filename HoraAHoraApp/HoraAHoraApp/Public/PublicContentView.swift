import SwiftUI
import UIKit
import FeatureCalculator
import FeatureScoreTable
import FeatureSettings

struct PublicContentView: View {
    let dependencies: PublicAppDependencies

    @State private var presentedLink: PresentedLink?
    @Environment(\.openURL) private var openURL
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        StartupLoadingContainer {
            TabView {
                CalculatorRootView(
                    repository: dependencies.core.chatRepository,
                    sharing: dependencies.core.conversationSharing
                )
                .calculatorTabItem()

                ComparatorRootView()
                    .comparatorTabItem()

                ScoreTableRootView()
                    .scoreTableTabItem()

                SettingsRootView(
                    model: dependencies.core.settingsModel,
                    configuration: dependencies.core.configuration.settingsConfiguration,
                    onOpenURL: { url in presentedLink = PresentedLink(url: url) },
                    onContactSupport: { url in openURL(url) },
                    onCopyIdentifier: { identifier in UIPasteboard.general.string = identifier }
                )
                .settingsTabItem()
            }
        }
        // At launch and whenever the app comes back to the foreground; once done, it returns
        // at once.
        .task(id: scenePhase) {
            guard scenePhase == .active else { return }
            await dependencies.legacyNewsNotifications.retireIfNeeded()
        }
        .inAppBrowser(for: $presentedLink)
    }
}
