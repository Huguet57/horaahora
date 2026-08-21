import Foundation
import XCTest
import CastellsDomain
@testable import FeatureCalculator

final class ScorePresentationTests: XCTestCase {
    func testBuildsRankingRowsFromStructuredResponse() throws {
        let response = try Self.decode(
            presentation: #"""
            {
              "type":"score_ranking",
              "title":"Rànquing de puntuacions 2026",
              "outcome":"both",
              "focus_notation":null,
              "rows":[
                {"position":1,"notation":"3de10sm","loaded_points":6205,"unloaded_points":7475},
                {"position":2,"notation":"4de10sm","loaded_points":5910,"unloaded_points":7120}
              ]
            }
            """#
        )

        let presentation = try XCTUnwrap(ScorePresentation(response: response))

        XCTAssertEqual(presentation.title, "Rànquing de puntuacions 2026")
        XCTAssertEqual(presentation.outcome, .both)
        XCTAssertNil(presentation.focusNotation)
        XCTAssertEqual(presentation.rows.map(\.notation), ["3de10sm", "4de10sm"])
        XCTAssertEqual(presentation.rows.map(\.unloadedPoints), [7_475, 7_120])
    }

    func testBuildsFocusedRankingWithNeighbors() throws {
        let response = try Self.decode(
            presentation: #"""
            {
              "type":"score_ranking",
              "title":"Pde7sf · 4a posició",
              "outcome":"both",
              "focus_notation":"Pde7sf",
              "rows":[
                {"position":3,"notation":"2de10fmp","loaded_points":5630,"unloaded_points":6780},
                {"position":4,"notation":"Pde7sf","loaded_points":5280,"unloaded_points":6360},
                {"position":5,"notation":"3de9sf","loaded_points":5165,"unloaded_points":6220}
              ]
            }
            """#
        )

        let presentation = try XCTUnwrap(ScorePresentation(response: response))

        XCTAssertEqual(presentation.focusNotation, "Pde7sf")
        XCTAssertEqual(presentation.rows.map(\.position), [3, 4, 5])
        XCTAssertEqual(presentation.rows.map(\.notation), ["2de10fmp", "Pde7sf", "3de9sf"])
    }

    func testRejectsLegacyScoreCards() throws {
        let response = try Self.decode(
            presentation: #"""
            {
              "type":"score_card",
              "title":"Fitxa antiga",
              "outcome":"both",
              "focus_notation":null,
              "rows":[]
            }
            """#
        )

        XCTAssertNil(ScorePresentation(response: response))
    }

    private static func decode(presentation: String) throws -> ChatResponse {
        let json = """
        {
          "reply":"Resposta de compatibilitat.",
          "intent":"contest_info",
          "performances":[],
          "winner_label":null,
          "warnings":[],
          "ruleset_version":"concurs-2026",
          "needs_clarification":false,
          "presentation":\(presentation)
        }
        """
        return try JSONDecoder.castellsAPI.decode(ChatResponse.self, from: Data(json.utf8))
    }
}
