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
        XCTAssertNil(presentation?.notCountedNote)
    }

    func testNoteSaysWhichCastellsDoNotCountAndWhy() {
        // Shared conversations: a castell that stopped counting looked like the calculator ignored it.
        func castell(
            _ canonical: String,
            _ outcome: String,
            _ points: Int,
            reason: String? = nil
        ) -> ScoredCastellResponse {
            ScoredCastellResponse(
                input: canonical,
                canonical: canonical,
                outcome: outcome,
                points: points,
                counted: reason == nil,
                reason: reason
            )
        }
        let response = ChatResponse(
            reply: "Joves: Pde7sf carregat, 3de9sf carregat. Total: 10.445 punts.",
            intent: "total",
            performances: [
                PerformanceResponse(
                    label: "Joves",
                    total: 10_445,
                    castells: [
                        castell("Pde7sf", "loaded", 5_280),
                        castell("3de9sf", "loaded", 5_165),
                        castell("3de10fm", "loaded", 3_755, reason: "loaded_limit"),
                        castell("2de9sm", "loaded", 4_685, reason: "loaded_limit"),
                        castell("3de9f", "unloaded", 1_910, reason: "duplicate_structure"),
                        castell("5de8", "unloaded", 1_385, reason: "outside_top_three"),
                        castell("4de9f", "attempt", 0, reason: "attempt"),
                    ]
                )
            ],
            winnerLabel: nil,
            warnings: [],
            rulesetVersion: "concurs-2026",
            needsClarification: false
        )

        let presentation = PerformanceSummaryPresentation(response: response)

        XCTAssertEqual(
            presentation?.notCountedNote,
            "No compten: 3de10fm i 2de9sm (només compten 2 carregats), 3de9f (repetit), "
                + "5de8 (fora de les 3 millors)."
        )
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
