import XCTest
@testable import CastellsDomain

final class ElMonCastellerContractTests: XCTestCase {
    func testRSSArticleDecodesAndOpensItsOriginalURL() throws {
        let json = #"""
        {
          "items": [{
            "id": "item-1",
            "source_id": "el-mon-casteller",
            "external_id": "external-1",
            "title": "Una diada & una estrena",
            "display_title": "Una diada & una estrena",
            "summary": "Una estrena a plaça …",
            "published_at": "2026-09-24T09:08:17Z",
            "source_order": 0,
            "article_url": "https://www.elmoncasteller.cat/una-diada/",
            "action_url": "https://www.elmoncasteller.cat/una-diada/",
            "attribution": "El Món Casteller",
            "created_at": "2026-09-24T10:00:00.123456Z",
            "updated_at": "2026-09-24T10:00:00.123456Z"
          }],
          "next_cursor": null,
          "from_cache": true
        }
        """#.data(using: .utf8)!

        let page = try JSONDecoder.castellsAPI.decode(HourByHourPage.self, from: json)
        let item = try XCTUnwrap(page.items.first)

        XCTAssertEqual(item.sourceID, "el-mon-casteller")
        XCTAssertEqual(item.summary, "Una estrena a plaça …")
        XCTAssertEqual(item.attribution, "El Món Casteller")
        XCTAssertNotNil(item.publishedAt)
        XCTAssertEqual(item.associatedURL, item.articleURL)
        XCTAssertTrue(page.fromCache)
    }
}
