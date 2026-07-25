import XCTest
@testable import CastellsDomain

final class GroupDirectoryContractTests: XCTestCase {
    func testDecodesTheProviderNeutralContract() throws {
        let json = #"""
        {
          "groups": ["Castellers de Vilafranca", "Colla Vella dels Xiquets de Valls"],
          "revision": "2026-07-25",
          "official_url": "https://castellscat.cat/public/ca/les-colles-llistat"
        }
        """#.data(using: .utf8)!

        let directory = try JSONDecoder.castellsAPI.decode(
            CastellerGroupDirectory.self,
            from: json
        )

        XCTAssertEqual(directory.groups.first, "Castellers de Vilafranca")
        XCTAssertEqual(directory.revision, "2026-07-25")
        XCTAssertEqual(directory.officialURL.host, "castellscat.cat")
    }
}
