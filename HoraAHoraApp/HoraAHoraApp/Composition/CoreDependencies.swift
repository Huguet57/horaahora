import Foundation
import SwiftData
import CastellsData
import CastellsDomain
import FeatureSettings

/// What both apps build: the local storage, the API client and the calculator with its settings.
/// Each app's dependencies add their own sections on top.
@MainActor
final class CoreDependencies {
    let configuration: AppConfiguration
    /// The whole SwiftData schema, Hora a Hora and Agenda caches included, in both apps: the
    /// public app keeps the store of the versions that had them, with its conversations.
    let modelContainer: ModelContainer
    let apiClient: APIClient
    let chatRepository: any ChatRepository
    let conversationSharing: any ConversationSharingPreferences
    let settingsModel: SettingsModel

    var settingsConfiguration: SettingsConfiguration {
        configuration.settingsConfiguration
    }

    init(configuration: AppConfiguration, userDefaults: UserDefaults) throws {
        self.configuration = configuration
        modelContainer = try DataStack.makeModelContainer()
        apiClient = APIClient(baseURL: configuration.apiBaseURL)
        let conversationSharing = ConversationSharingStore(userDefaults: userDefaults)
        chatRepository = SwiftDataChatRepository(
            container: modelContainer,
            remoteService: HTTPChatRemoteService(client: apiClient),
            installationID: configuration.technicalIdentifier,
            sharing: conversationSharing
        )
        self.conversationSharing = conversationSharing
        settingsModel = SettingsModel(conversationSharing: conversationSharing)
    }
}
