import XCTest
import CastellsDomain
@testable import FeatureCalculator

final class PerformanceSummaryPresentationTests: XCTestCase {
    func testBuildsRowsAndTotalForASingleCalculatedPerformance() {
        let response = ChatResponse(
            reply: "Total: 20.615 punts.",
            intent: "total",
            performances: [
                PerformanceResponse(
                    label: "Actuació",
                    total: 20_615,
                    castells: [
                        ScoredCastellResponse(
                            input: "3d10sm",
                            canonical: "3de10sm",
                            outcome: "unloaded",
                            points: 7_475,
                            counted: true,
                            reason: nil
                        ),
                        ScoredCastellResponse(
                            input: "2d10fmp",
                            canonical: "2de10fmp",
                            outcome: "unloaded",
                            points: 6_780,
                            counted: true,
                            reason: nil
                        ),
                    ]
                )
            ],
            winnerLabel: nil,
            warnings: [],
            rulesetVersion: "concurs-2026",
            needsClarification: false
        )

        let presentation = PerformanceSummaryPresentation(response: response)

        XCTAssertEqual(presentation?.title, "Actuació calculada")
        XCTAssertEqual(presentation?.rows.map(\.notation), ["3de10sm", "2de10fmp"])
        XCTAssertEqual(presentation?.rows.first?.result, "Descarregat")
        XCTAssertEqual(presentation?.total, 20_615)
    }

    func testDoesNotReplaceComparisonPresentation() {
        let response = ChatResponse(
            reply: "Comparació",
            intent: "comparison",
            performances: [],
            winnerLabel: nil,
            warnings: [],
            rulesetVersion: "concurs-2026",
            needsClarification: false
        )

        XCTAssertNil(PerformanceSummaryPresentation(response: response))
    }
}
