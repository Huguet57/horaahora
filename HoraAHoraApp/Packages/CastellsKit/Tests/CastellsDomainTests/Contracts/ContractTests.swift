import XCTest
@testable import CastellsDomain

final class ContractTests: XCTestCase {
    func testChatRequestSendsTheSharingChoice() throws {
        let request = ChatRequest(
            conversationID: UUID(uuidString: "3A35386D-F0E4-49CC-86D2-18FAC079645C")!,
            installationID: "installation",
            messages: [ChatRequestMessage(role: .user, content: "5d9f o 4d9fa?")],
            shareForImprovement: true
        )

        let data = try JSONEncoder.castellsAPI.encode(request)
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])

        XCTAssertEqual(json["share_for_improvement"] as? Bool, true)
        XCTAssertEqual(json["conversation_id"] as? String, "3A35386D-F0E4-49CC-86D2-18FAC079645C")
    }

    func testChatRequestIsPrivateByDefault() throws {
        let request = ChatRequest(
            conversationID: UUID(),
            installationID: "installation",
            messages: [ChatRequestMessage(role: .user, content: "5d9f o 4d9fa?")]
        )

        XCTAssertFalse(request.shareForImprovement)
    }

    func testChatResponseDecodesProviderNeutralContract() throws {
        let json = #"""
        {
          "reply":"Guanya Vella.",
          "intent":"comparison",
          "performances":[{
            "label":"Vella",
            "total":4930,
            "castells":[{
              "input":"4d10fm",
              "canonical":"4de10fm",
              "outcome":"unloaded",
              "points":4930,
              "counted":true,
              "reason":null
            }]
          }],
          "winner_label":"Vella",
          "warnings":[],
          "ruleset_version":"concurs-2026",
          "needs_clarification":false
        }
        """#.data(using: .utf8)!

        let decoder = JSONDecoder.castellsAPI
        let response = try decoder.decode(ChatResponse.self, from: json)

        XCTAssertEqual(response.winnerLabel, "Vella")
        XCTAssertEqual(response.performances.first?.castells.first?.points, 4930)
        XCTAssertNil(response.presentation)
    }

    func testChatResponseDecodesStructuredScorePresentation() throws {
        let json = #"""
        {
          "reply":"Els dos primers són el 3de10sm i el 4de10sm.",
          "intent":"contest_info",
          "performances":[],
          "winner_label":null,
          "warnings":[],
          "ruleset_version":"concurs-2026",
          "needs_clarification":false,
          "presentation":{
            "type":"score_ranking",
            "title":"Rànquing de puntuacions 2026",
            "outcome":"both",
            "focus_notation":null,
            "rows":[{
              "position":1,
              "notation":"3de10sm",
              "loaded_points":6205,
              "unloaded_points":7475
            }]
          }
        }
        """#.data(using: .utf8)!

        let response = try JSONDecoder.castellsAPI.decode(ChatResponse.self, from: json)

        XCTAssertEqual(response.presentation?.type, "score_ranking")
        XCTAssertEqual(response.presentation?.outcome, "both")
        XCTAssertEqual(response.presentation?.rows.first?.notation, "3de10sm")
        XCTAssertEqual(response.presentation?.rows.first?.unloadedPoints, 7_475)
    }
}
