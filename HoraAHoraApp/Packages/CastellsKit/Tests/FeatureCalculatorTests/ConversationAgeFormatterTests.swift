import Foundation
import XCTest
@testable import FeatureCalculator

final class ConversationAgeFormatterTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 1_000_000)

    func testUsesMinutesAsTheSmallestUnit() {
        XCTAssertEqual(formattedAge(secondsAgo: 5), "menys d’1 min")
        XCTAssertEqual(formattedAge(secondsAgo: 29 * 60 + 21), "29 min")
        XCTAssertEqual(formattedAge(secondsAgo: 34 * 60 + 6), "34 min")
    }

    func testKeepsAtMostTwoNonZeroUnits() {
        XCTAssertEqual(formattedAge(secondsAgo: 60 * 60), "1 h")
        XCTAssertEqual(formattedAge(secondsAgo: 60 * 60 + 60), "1 h i 1 min")
        XCTAssertEqual(formattedAge(secondsAgo: 2 * 24 * 60 * 60 + 9 * 60 * 60), "2 dies i 9 h")
    }

    func testUsesTheSingularDayLabel() {
        XCTAssertEqual(formattedAge(secondsAgo: 24 * 60 * 60), "1 dia")
    }

    private func formattedAge(secondsAgo: TimeInterval) -> String {
        ConversationAgeFormatter.string(
            from: now.addingTimeInterval(-secondsAgo),
            relativeTo: now
        )
    }
}
