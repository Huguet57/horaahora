import Foundation
import SwiftData
import CastellsData
import CastellsDomain
import FeatureSettings

/// What both apps build: the local storage, the API clients and the calculator with its
/// settings. Each app's dependencies add their own sections on top.
@MainActor
final class CoreDependencies {
    let configuration: AppConfiguration
    let modelContainer: ModelContainer
    let apiClient: APIClient
    /// Subscriptions to the news notifications, under this app's bundle identifier: the internal
    /// app subscribes, and the public app unsubscribes what an earlier version left.
    let pushSubscriptions: any PushSubscriptionRemoteService
    let chatRepository: any ChatRepository
    let conversationSharing: any ConversationSharingPreferences
    let settingsModel: SettingsModel

    init(configuration: AppConfiguration, userDefaults: UserDefaults) throws {
        self.configuration = configuration
        modelContainer = try DataStack.makeModelContainer()
        apiClient = APIClient(baseURL: configuration.apiBaseURL)
        pushSubscriptions = HTTPPushSubscriptionRemoteService(
            client: apiClient,
            appID: configuration.bundleIdentifier
        )
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
