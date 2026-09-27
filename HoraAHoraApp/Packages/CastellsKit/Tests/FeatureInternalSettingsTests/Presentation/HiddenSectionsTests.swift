import XCTest
import CastellsDomain
@testable import FeatureInternalSettings

@MainActor
final class HiddenSectionsTests: XCTestCase {
    private let start = Date(timeIntervalSince1970: 1_790_500_000)

    func testSevenQuickTapsShowTheHiddenSectionsAndSevenMoreHideThem() {
        let clock = TapClock(now: start)
        let preferences = HiddenSectionsStub()
        let model = makeModel(preferences: preferences, clock: clock)
        XCTAssertFalse(model.showsHiddenSections)

        XCTAssertEqual(tap(model, times: 6, clock: clock), [false, false, false, false, false, false])
        XCTAssertFalse(model.showsHiddenSections)
        XCTAssertTrue(tapOnce(model, clock: clock))
        XCTAssertTrue(model.showsHiddenSections)
        XCTAssertTrue(preferences.isUnlocked)

        _ = tap(model, times: 6, clock: clock)
        XCTAssertTrue(tapOnce(model, clock: clock))
        XCTAssertFalse(model.showsHiddenSections)
        XCTAssertFalse(preferences.isUnlocked)
    }

    func testTheVersionRowSaysWhatTheGestureDid() {
        let clock = TapClock(now: start)
        let model = makeModel(preferences: HiddenSectionsStub(), clock: clock)

        XCTAssertEqual(versionTaps(model, times: 6, clock: clock), [String?](repeating: nil, count: 6))
        XCTAssertEqual(versionTaps(model, times: 1, clock: clock), ["S'han activat Hora a Hora i Agenda"])
        XCTAssertEqual(versionTaps(model, times: 6, clock: clock), [String?](repeating: nil, count: 6))
        XCTAssertEqual(versionTaps(model, times: 1, clock: clock), ["S'han amagat Hora a Hora i Agenda"])
    }

    func testAPauseStartsTheSequenceAgain() {
        let clock = TapClock(now: start)
        let model = makeModel(preferences: HiddenSectionsStub(), clock: clock)
        _ = tap(model, times: 6, clock: clock)

        clock.now += 2
        XCTAssertFalse(tapOnce(model, clock: clock))
        _ = tap(model, times: 5, clock: clock)
        XCTAssertFalse(model.showsHiddenSections)

        XCTAssertTrue(tapOnce(model, clock: clock))
        XCTAssertTrue(model.showsHiddenSections)
    }

    func testUsersWhoAlreadyGetNewsKeepTheHiddenSections() async {
        let preferences = HiddenSectionsStub()
        let model = InternalSettingsModel(
            notificationManager: StatusStub(status: .enabled),
            hiddenSections: preferences
        )

        await model.refreshNotificationStatus()

        XCTAssertEqual(preferences.resolvedDefaults, [true])
        XCTAssertTrue(model.showsHiddenSections)
    }

    func testEverybodyElseStartsWithoutThem() async {
        let preferences = HiddenSectionsStub()
        let model = InternalSettingsModel(
            notificationManager: StatusStub(status: .notDetermined),
            hiddenSections: preferences
        )

        await model.refreshNotificationStatus()

        XCTAssertEqual(preferences.resolvedDefaults, [false])
        XCTAssertFalse(model.showsHiddenSections)
    }

    func testWithoutPreferencesTheSectionsStayHidden() {
        let clock = TapClock(now: start)
        let model = makeModel(preferences: nil, clock: clock)

        XCTAssertEqual(tap(model, times: 7, clock: clock).filter { $0 }, [])
        XCTAssertFalse(model.showsHiddenSections)
    }

    private func makeModel(preferences: HiddenSectionsStub?, clock: TapClock) -> InternalSettingsModel {
        InternalSettingsModel(
            notificationManager: StatusStub(status: .notDetermined),
            hiddenSections: preferences,
            now: clock.read
        )
    }

    private func tap(_ model: InternalSettingsModel, times: Int, clock: TapClock) -> [Bool] {
        (0..<times).map { _ in tapOnce(model, clock: clock) }
    }

    private func versionTaps(_ model: InternalSettingsModel, times: Int, clock: TapClock) -> [String?] {
        (0..<times).map { _ in
            clock.now += 0.4
            return model.versionTapMessage()
        }
    }

    private func tapOnce(_ model: InternalSettingsModel, clock: TapClock) -> Bool {
        clock.now += 0.4
        return model.registerSecretTap()
    }
}

@MainActor
private final class TapClock {
    var now: Date

    init(now: Date) {
        self.now = now
    }

    func read() -> Date { now }
}

@MainActor
private final class HiddenSectionsStub: HiddenSectionsPreferences {
    private(set) var isUnlocked = false
    private(set) var resolvedDefaults: [Bool] = []

    func setUnlocked(_ unlocked: Bool) { isUnlocked = unlocked }

    func resolveDefault(notificationsEnabled: Bool) {
        resolvedDefaults.append(notificationsEnabled)
        isUnlocked = notificationsEnabled
    }
}

@MainActor
private final class StatusStub: HourByHourNotificationManaging {
    let status: HourByHourNotificationStatus
    var minimumInterest: NotificationInterestLevel = .high

    init(status: HourByHourNotificationStatus) {
        self.status = status
    }

    func setMinimumInterest(_ value: NotificationInterestLevel) async {}
    func synchronizationPending() async -> Bool { false }
    func currentStatus() async -> HourByHourNotificationStatus { status }
    func enable() async throws -> HourByHourNotificationStatus { .enabled }
    func disable() async throws -> HourByHourNotificationStatus { .disabled }
    func openSystemSettings() async {}
}
