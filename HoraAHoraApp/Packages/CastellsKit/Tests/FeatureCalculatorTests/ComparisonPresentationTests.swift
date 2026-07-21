import Foundation
import XCTest
import CastellsDomain
@testable import FeatureCalculator

final class ComparisonPresentationTests: XCTestCase {
    func testBuildsAComparisonWithCastellsTotalsWinnerAndMargin() throws {
        let response = try JSONDecoder.castellsAPI.decode(
            ChatResponse.self,
            from: Data(Self.responseJSON.utf8)
        )

        let presentation = try XCTUnwrap(ComparisonPresentation(response: response))

        XCTAssertEqual(presentation.columns.map(\.label), ["Vella", "Joves"])
        XCTAssertEqual(presentation.columns[0].castells[0].notation, "4de10fm")
        XCTAssertEqual(presentation.columns[0].castells[0].result, "Descarregat")
        XCTAssertEqual(presentation.columns.map(\.total), [4_930, 4_105])
        XCTAssertEqual(presentation.winnerLabel, "Vella")
        XCTAssertEqual(presentation.margin, 825)
        XCTAssertEqual(presentation.summary, "Guanya Vella per 825 punts.")
        XCTAssertEqual(presentation.maximumCastellCount, 1)
    }

    func testOnlyBuildsForComparisonsWithAtLeastTwoPerformances() throws {
        let response = try JSONDecoder.castellsAPI.decode(
            ChatResponse.self,
            from: Data(Self.responseJSON.replacingOccurrences(
                of: #""intent": "comparison""#,
                with: #""intent": "total""#
            ).utf8)
        )

        XCTAssertNil(ComparisonPresentation(response: response))
    }

    private static let responseJSON = #"""
    {
      "reply": "Guanya Vella per 825 punts.",
      "intent": "comparison",
      "performances": [
        {
          "label": "Vella",
          "total": 4930,
          "castells": [
            {
              "input": "4d10fm",
              "canonical": "4de10fm",
              "outcome": "unloaded",
              "points": 4930,
              "counted": true,
              "reason": null
            }
          ]
        },
        {
          "label": "Joves",
          "total": 4105,
          "castells": [
            {
              "input": "4d9net",
              "canonical": "4de9sf",
              "outcome": "unloaded",
              "points": 4105,
              "counted": true,
              "reason": null
            }
          ]
        }
      ],
      "winner_label": "Vella",
      "warnings": [],
      "ruleset_version": "concurs-2026",
      "needs_clarification": false
    }
    """#
}
