import Foundation
import CastellsDomain

@MainActor
public final class ConversationSharingStore: ConversationSharingPreferences {
    private enum Key {
        static let enabled = "castells.conversation-sharing.enabled"
        static let noticeAcknowledged = "castells.conversation-sharing.notice-acknowledged"
        static let startedAt = "castells.conversation-sharing.started-at"
    }

    private let userDefaults: UserDefaults
    private let now: @MainActor () -> Date

    public init(
        userDefaults: UserDefaults = .standard,
        now: @escaping @MainActor () -> Date = { .now }
    ) {
        self.userDefaults = userDefaults
        self.now = now
    }

    public var isEnabled: Bool {
        userDefaults.object(forKey: Key.enabled) as? Bool ?? true
    }

    public var isNoticeAcknowledged: Bool {
        userDefaults.bool(forKey: Key.noticeAcknowledged)
    }

    public func setEnabled(_ enabled: Bool) {
        guard enabled != isEnabled else { return }
        userDefaults.set(enabled, forKey: Key.enabled)
        // Turning sharing back on only covers conversations started from now on.
        if enabled { userDefaults.set(now(), forKey: Key.startedAt) }
    }

    public func noticeWasShown() {
        guard isEnabled, startedAt == nil else { return }
        userDefaults.set(now(), forKey: Key.startedAt)
    }

    public func acknowledgeNotice() {
        userDefaults.set(true, forKey: Key.noticeAcknowledged)
    }

    public func sharesConversation(createdAt: Date) -> Bool {
        guard isEnabled, let startedAt else { return false }
        return createdAt >= startedAt
    }

    private var startedAt: Date? {
        userDefaults.object(forKey: Key.startedAt) as? Date
    }
}
