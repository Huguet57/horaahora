import SwiftUI
import FeatureSettings

/// Ajustos in the internal app: the calculator's settings, plus the news notifications and the
/// sources of Hora a Hora and Agenda while those sections show, and the secret gesture on the
/// version row.
public struct InternalSettingsRootView: View {
    private let model: InternalSettingsModel
    private let settingsModel: SettingsModel
    private let configuration: SettingsConfiguration
    private let sources: InternalSources
    private let hasFollowedGroups: Bool
    private let onChooseGroups: () -> Void
    private let onOpenURL: (URL) -> Void
    private let onContactSupport: (URL) -> Void
    private let onCopyIdentifier: (String) -> Void

    public init(
        model: InternalSettingsModel,
        settingsModel: SettingsModel,
        configuration: SettingsConfiguration,
        sources: InternalSources,
        hasFollowedGroups: Bool,
        onChooseGroups: @escaping () -> Void,
        onOpenURL: @escaping (URL) -> Void,
        onContactSupport: @escaping (URL) -> Void,
        onCopyIdentifier: @escaping (String) -> Void
    ) {
        self.model = model
        self.settingsModel = settingsModel
        self.configuration = configuration
        self.sources = sources
        self.hasFollowedGroups = hasFollowedGroups
        self.onChooseGroups = onChooseGroups
        self.onOpenURL = onOpenURL
        self.onContactSupport = onContactSupport
        self.onCopyIdentifier = onCopyIdentifier
    }

    public var body: some View {
        SettingsRootView(
            model: settingsModel,
            configuration: configuration,
            additionalCredits: model.showsHiddenSections ? sources.credits : [],
            onVersionTap: { model.versionTapMessage() },
            onOpenURL: onOpenURL,
            onContactSupport: onContactSupport,
            onCopyIdentifier: onCopyIdentifier
        ) {
            if model.showsHiddenSections {
                NotificationSettingsSection(
                    model: model,
                    hasFollowedGroups: hasFollowedGroups,
                    onChooseGroups: onChooseGroups
                )
            }
        }
        .task {
            await model.refreshNotificationStatus()
        }
    }
}
