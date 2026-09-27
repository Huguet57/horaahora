import Foundation

/// Where the news notifications and the hidden sections keep their settings in UserDefaults.
/// Earlier versions of the public app wrote them and the internal app still does; the public
/// app looks for them to retire the notifications an earlier version turned on.
public enum NewsNotificationKeys {
    public static let enabled = "castells.hour-by-hour.notifications-enabled"
    public static let minimumInterest = "castells.hour-by-hour.minimum-interest.v1"
    public static let onboardingDismissed = "castells.hour-by-hour.notification-onboarding-dismissed"
    public static let sectionsUnlocked = "castells.hidden-sections.unlocked"

    static let all = [enabled, minimumInterest, onboardingDismissed, sectionsUnlocked]
}
