import SwiftUI
import UIKit
import FeatureCalculator
import FeatureScoreTable
import FeatureSettings

struct ContentView: View {
    let dependencies: AppDependencies

    @State private var presentedLink: PresentedLink?
    @Environment(\.openURL) private var openURL

    var body: some View {
        StartupLoadingContainer {
            TabView {
                CalculatorRootView(
                    repository: dependencies.chatRepository,
                    sharing: dependencies.conversationSharing
                )
                .calculatorTabItem()

                ComparatorRootView()
                    .comparatorTabItem()

                ScoreTableRootView()
                    .scoreTableTabItem()

                SettingsRootView(
                    model: dependencies.settingsModel,
                    configuration: dependencies.configuration.settingsConfiguration,
                    onOpenURL: { url in presentedLink = PresentedLink(url: url) },
                    onContactSupport: { url in openURL(url) },
                    onCopyIdentifier: { identifier in UIPasteboard.general.string = identifier }
                )
                .settingsTabItem()
            }
        }
        .inAppBrowser(for: $presentedLink)
    }
}
