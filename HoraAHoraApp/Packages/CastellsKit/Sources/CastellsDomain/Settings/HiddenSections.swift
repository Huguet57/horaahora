import Foundation

/// Whether the app shows the sections it hides by default: Hora a Hora, Agenda and their
/// settings. A secret gesture in Ajustos shows and hides them.
@MainActor
public protocol HiddenSectionsPreferences: AnyObject {
    var isUnlocked: Bool { get }
    func setUnlocked(_ unlocked: Bool)
    /// The first time the notification status is known, users who already receive news
    /// notifications keep the sections; everybody else starts without them.
    func resolveDefault(notificationsEnabled: Bool)
}
