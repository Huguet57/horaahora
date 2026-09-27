import Foundation

/// Whether calculator conversations are shared with the backend to improve the product.
///
/// Sharing is on by default, but it only covers conversations started after the user has
/// seen the notice (or turned sharing back on), so nothing written under an earlier promise
/// is sent retroactively.
@MainActor
public protocol ConversationSharingPreferences: AnyObject {
    var isEnabled: Bool { get }
    var isNoticeAcknowledged: Bool { get }
    func setEnabled(_ enabled: Bool)
    func noticeWasShown()
    func acknowledgeNotice()
    func sharesConversation(createdAt: Date) -> Bool
}
