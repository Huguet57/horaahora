import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class ConversationSharingStoreTests: XCTestCase {
    private let noticeShownAt = Date(timeIntervalSince1970: 1_790_500_000)

    func testSharingIsOnByDefaultButOnlyStartsOnceTheNoticeIsShown() {
        let clock = Clock(now: noticeShownAt)
        let store = ConversationSharingStore(userDefaults: freshDefaults(), now: clock.read)

        XCTAssertTrue(store.isEnabled)
        XCTAssertFalse(store.isNoticeAcknowledged)
        XCTAssertFalse(store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(60)))

        store.noticeWasShown()

        XCTAssertTrue(store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(60)))
        XCTAssertFalse(
            store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(-60)),
            "Conversations written before the notice were promised not to be stored"
        )
    }

    func testShowingTheNoticeAgainDoesNotMoveTheStart() {
        let clock = Clock(now: noticeShownAt)
        let store = ConversationSharingStore(userDefaults: freshDefaults(), now: clock.read)
        store.noticeWasShown()

        clock.now = noticeShownAt.addingTimeInterval(3_600)
        store.noticeWasShown()

        XCTAssertTrue(store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(60)))
    }

    func testTurningSharingOffStopsItImmediately() {
        let store = ConversationSharingStore(
            userDefaults: freshDefaults(),
            now: Clock(now: noticeShownAt).read
        )
        store.noticeWasShown()

        store.setEnabled(false)

        XCTAssertFalse(store.isEnabled)
        XCTAssertFalse(store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(60)))
    }

    func testTurningSharingBackOnOnlyCoversNewConversations() {
        let clock = Clock(now: noticeShownAt)
        let store = ConversationSharingStore(userDefaults: freshDefaults(), now: clock.read)
        store.noticeWasShown()
        store.setEnabled(false)

        let reenabledAt = noticeShownAt.addingTimeInterval(3_600)
        clock.now = reenabledAt
        store.setEnabled(true)

        XCTAssertFalse(store.sharesConversation(createdAt: reenabledAt.addingTimeInterval(-60)))
        XCTAssertTrue(store.sharesConversation(createdAt: reenabledAt.addingTimeInterval(60)))
    }

    func testDisablingBeforeTheNoticeKeepsSharingOff() {
        let store = ConversationSharingStore(
            userDefaults: freshDefaults(),
            now: Clock(now: noticeShownAt).read
        )
        store.setEnabled(false)

        store.noticeWasShown()

        XCTAssertFalse(store.sharesConversation(createdAt: noticeShownAt.addingTimeInterval(60)))
    }

    func testChoicesPersistAcrossLaunches() {
        let defaults = freshDefaults()
        let store = ConversationSharingStore(userDefaults: defaults, now: Clock(now: noticeShownAt).read)
        store.noticeWasShown()
        store.acknowledgeNotice()
        store.setEnabled(false)

        let restored = ConversationSharingStore(userDefaults: defaults)

        XCTAssertFalse(restored.isEnabled)
        XCTAssertTrue(restored.isNoticeAcknowledged)
    }

    private func freshDefaults() -> UserDefaults {
        UserDefaults(suiteName: UUID().uuidString)!
    }
}

@MainActor
private final class Clock {
    var now: Date

    init(now: Date) {
        self.now = now
    }

    func read() -> Date { now }
}
