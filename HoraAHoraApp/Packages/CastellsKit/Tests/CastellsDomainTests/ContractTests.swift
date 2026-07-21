import XCTest
@testable import CastellsDomain

final class ContractTests: XCTestCase {
    func testHourByHourPageDecodesFastAPIDatesWithFractionalSeconds() throws {
        let json = #"""
        {
          "items": [{
            "id": "item-1",
            "source_id": "revista-castells",
            "external_id": "external-1",
            "title": "Entrada",
            "display_title": "Entrada",
            "summary": "Resum",
            "published_at": "2026-07-20T12:45:22+00:00",
            "source_order": 0,
            "article_url": "https://example.com/article",
            "action_url": null,
            "attribution": "Revista Castells",
            "created_at": "2026-07-20T12:54:09.737320+00:00",
            "updated_at": "2026-07-20T12:54:09.737320+00:00"
          }],
          "next_cursor": null,
          "from_cache": false
        }
        """#.data(using: .utf8)!

        let page = try JSONDecoder.castellsAPI.decode(HourByHourPage.self, from: json)

        XCTAssertEqual(page.items.first?.externalID, "external-1")
        XCTAssertEqual(page.items.first?.displayTitle, "Entrada")
        XCTAssertNil(page.items.first?.actionURL)
        XCTAssertNotNil(page.items.first?.createdAt)
    }

    func testHourByHourItemOnlyExposesADedicatedAssociatedLink() {
        let articleURL = URL(string: "https://example.com/article")!
        let actionURL = URL(string: "https://example.com/action")!
        let now = Date()
        let linked = HourByHourItem(
            id: "linked",
            sourceID: "source",
            externalID: "linked",
            title: "Amb enllaç",
            displayTitle: "Amb enllaç",
            summary: "",
            publishedAt: now,
            sourceOrder: 0,
            articleURL: articleURL,
            actionURL: actionURL,
            attribution: "Font",
            createdAt: now,
            updatedAt: now
        )
        let legacyFallback = HourByHourItem(
            id: "fallback",
            sourceID: "source",
            externalID: "fallback",
            title: "Sense enllaç",
            displayTitle: "Sense enllaç",
            summary: "",
            publishedAt: now,
            sourceOrder: 1,
            articleURL: articleURL,
            actionURL: articleURL,
            attribution: "Font",
            createdAt: now,
            updatedAt: now
        )

        XCTAssertEqual(linked.associatedURL, actionURL)
        XCTAssertNil(legacyFallback.associatedURL)
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
    }

    func testAgendaDecodesImpreciseTimeAndNeutralSourceStatus() throws {
        let json = #"""
        {
          "items": [{
            "id": "event-1",
            "source_id": "cccc",
            "external_id": "external-1",
            "title": "Diada",
            "local_date": "2026-07-21",
            "starts_at": null,
            "time_label": "Tarda",
            "timezone": "Europe/Madrid",
            "venue": "Plaça",
            "municipality": "Valls",
            "participating_groups": ["Colla A"],
            "notes": "",
            "source_url": "https://castellscat.cat/ca/agenda?a=2026&m=07",
            "source_order": 0,
            "attribution": "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
            "revision": "r1",
            "updated_at": "2026-07-21T10:00:00Z"
          }],
          "next_cursor": null,
          "official_url": "https://castellscat.cat/ca/agenda",
          "from_cache": false,
          "source_status": "active"
        }
        """#.data(using: .utf8)!

        let page = try JSONDecoder.castellsAPI.decode(AgendaPage.self, from: json)

        XCTAssertEqual(page.items.first?.localDate, "2026-07-21")
        XCTAssertEqual(page.items.first?.timeLabel, "Tarda")
        XCTAssertNil(page.items.first?.startsAt)
        XCTAssertEqual(page.sourceStatus, .active)
    }
}
