import Foundation
import SwiftData
import CastellsData
import CastellsDomain
import FeatureSettings

/// The composition root: the local storage, the API client and the calculator with its settings.
@MainActor
final class AppDependencies {
    let configuration: AppConfiguration
    let modelContainer: ModelContainer
    let apiClient: APIClient
    let chatRepository: any ChatRepository
    let conversationSharing: any ConversationSharingPreferences
    let settingsModel: SettingsModel

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
