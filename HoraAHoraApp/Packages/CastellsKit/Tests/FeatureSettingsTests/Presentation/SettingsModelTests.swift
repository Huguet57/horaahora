import XCTest
import CastellsDomain
@testable import FeatureSettings

@MainActor
final class SettingsModelTests: XCTestCase {
    func testConversationSharingToggleWritesThroughAndRefreshes() {
        let sharing = SharingPreferencesStub()
        let model = SettingsModel(conversationSharing: sharing)
        XCTAssertTrue(model.showsConversationSharing)
        XCTAssertTrue(model.isConversationSharingEnabled)

        model.setConversationSharingEnabled(false)

        XCTAssertFalse(sharing.isEnabled)
        XCTAssertFalse(model.isConversationSharingEnabled)

        sharing.setEnabled(true)
        model.refreshConversationSharing()

        XCTAssertTrue(model.isConversationSharingEnabled)
    }

    func testConversationSharingIsHiddenWithoutPreferences() {
        let model = SettingsModel()

        XCTAssertFalse(model.showsConversationSharing)
        XCTAssertFalse(model.isConversationSharingEnabled)
    }
}

@MainActor
private final class SharingPreferencesStub: ConversationSharingPreferences {
    private(set) var isEnabled = true
    var isNoticeAcknowledged: Bool { false }

    func setEnabled(_ enabled: Bool) { isEnabled = enabled }
    func noticeWasShown() {}
    func acknowledgeNotice() {}
    func sharesConversation(createdAt: Date) -> Bool { isEnabled }
}
