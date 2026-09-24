import XCTest
import CastellsDomain
@testable import CastellsData

final class PushPreferenceSyncTests: XCTestCase {
    func testChangingPreferencesWithSameTokenRegistersAgainAndRetriesFailure() async {
        let remote = PreferenceRemote()
        let coordinator = makeCoordinator(remote)
        await coordinator.setEnabled(true)
        await coordinator.didReceiveDeviceToken("token")
        await remote.failNext()
        await coordinator.setPreferences(minimumInterest: .medium,
            groupSelection: .init(mode: .custom, keys: ["Minyons"]))
        let pending = await coordinator.isSynchronizationPending
        XCTAssertTrue(pending)
        await coordinator.setEnabled(true)
        let synced = await coordinator.isSynchronizationPending
        XCTAssertFalse(synced)
        let requests = await remote.requests
        XCTAssertEqual(requests.count, 3)
        XCTAssertEqual(requests.last?.minimumInterest, .medium)
        XCTAssertEqual(requests.last?.groupSelection.keys, ["minyons"])
    }

    func testConcurrentChangesAreSerializedAndLatestSelectionWins() async {
        let remote = PreferenceRemote(suspendFirst: true)
        let coordinator = makeCoordinator(remote)
        await coordinator.setEnabled(true)
        let first = Task { await coordinator.didReceiveDeviceToken("token") }
        await remote.waitForFirstRequest()
        await coordinator.setPreferences(minimumInterest: .low, groupSelection: .init())
        await coordinator.setPreferences(minimumInterest: .medium,
            groupSelection: .init(mode: .custom, keys: ["a"]))
        await remote.release()
        await first.value
        let requests = await remote.requests
        XCTAssertEqual(requests.map(\.minimumInterest), [.high, .medium])
        let pending = await coordinator.isSynchronizationPending
        XCTAssertFalse(pending)
    }

    func testDisablingWhileRegistrationIsInFlightEndsUnregistered() async {
        let remote = PreferenceRemote(suspendFirst: true)
        let coordinator = makeCoordinator(remote)
        await coordinator.setEnabled(true)
        let first = Task { await coordinator.didReceiveDeviceToken("token") }
        await remote.waitForFirstRequest()
        await coordinator.setEnabled(false)
        await remote.release()
        await first.value
        let deletes = await remote.deletes
        XCTAssertEqual(deletes, 1)
    }

    private func makeCoordinator(_ remote: PreferenceRemote) -> PushSubscriptionCoordinator {
        .init(remoteService: remote, installationID: "test", appVersion: "1",
              locale: "ca", environment: "development")
    }
}

private actor PreferenceRemote: PushSubscriptionRemoteService {
    var requests: [PushSubscriptionRequest] = []
    var deletes = 0
    private var shouldFail = false
    private let suspendFirst: Bool
    private var releaseContinuation: CheckedContinuation<Void, Never>?
    private var startedContinuation: CheckedContinuation<Void, Never>?

    init(suspendFirst: Bool = false) { self.suspendFirst = suspendFirst }
    func failNext() { shouldFail = true }
    func waitForFirstRequest() async {
        if !requests.isEmpty { return }
        await withCheckedContinuation { startedContinuation = $0 }
    }
    func release() { releaseContinuation?.resume(); releaseContinuation = nil }
    func register(request: PushSubscriptionRequest) async throws {
        requests.append(request)
        if suspendFirst && requests.count == 1 {
            await withCheckedContinuation {
                releaseContinuation = $0
                startedContinuation?.resume()
                startedContinuation = nil
            }
        }
        if shouldFail { shouldFail = false; throw URLError(.notConnectedToInternet) }
    }
    func unregister(installationID: String, environment: String) async throws { deletes += 1 }
}
