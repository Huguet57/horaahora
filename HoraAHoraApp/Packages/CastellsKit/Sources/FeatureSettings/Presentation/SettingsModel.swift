import Foundation
import Observation
import CastellsDomain

/// The calculator's settings: whether its conversations help improve it.
@MainActor
@Observable
public final class SettingsModel {
    public private(set) var isConversationSharingEnabled: Bool

    private let conversationSharing: (any ConversationSharingPreferences)?

    public init(conversationSharing: (any ConversationSharingPreferences)? = nil) {
        self.conversationSharing = conversationSharing
        isConversationSharingEnabled = conversationSharing?.isEnabled ?? false
    }

    public var showsConversationSharing: Bool {
        conversationSharing != nil
    }

    public func setConversationSharingEnabled(_ enabled: Bool) {
        conversationSharing?.setEnabled(enabled)
        refreshConversationSharing()
    }

    /// The calculator's notice can also change the choice while Settings stays in memory.
    public func refreshConversationSharing() {
        isConversationSharingEnabled = conversationSharing?.isEnabled ?? false
    }
}
