import XCTest
import CastellsDomain
@testable import FeatureHourByHour

@MainActor
final class HourByHourViewModelTests: XCTestCase {
    func testRefreshStaysVisibleLongEnoughToAcknowledgeTheGesture() async {
        let repository = HourByHourRepositoryStub()
        let model = HourByHourViewModel(repository: repository)
        let clock = ContinuousClock()
        let startedAt = clock.now

        await model.refresh()

        let elapsed = startedAt.duration(to: clock.now)
        XCTAssertGreaterThanOrEqual(elapsed, .milliseconds(450))
        XCTAssertEqual(repository.forceRefreshRequests, [true])
        XCTAssertFalse(model.isLoading)
    }
}

@MainActor
private final class HourByHourRepositoryStub: HourByHourRepository {
    private(set) var forceRefreshRequests: [Bool] = []

    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        forceRefreshRequests.append(forceRefresh)
        return HourByHourPage(items: [], nextCursor: nil, fromCache: false)
    }
}
