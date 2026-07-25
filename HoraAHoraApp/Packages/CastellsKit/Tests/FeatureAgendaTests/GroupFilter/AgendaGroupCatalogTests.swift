import XCTest
@testable import FeatureAgenda

final class AgendaGroupCatalogTests: XCTestCase {
    func testMergesDisplayNamesAndKeepsTheirNormalizedKeysMaterialized() {
        let catalog = AgendaGroupCatalog(
            preferred: ["Colla A"],
            fallback: [
                "Castellers de la Vila de Gràcia",
                "CASTELLERS DE LA VILA DE GRACIA",
            ]
        )

        XCTAssertEqual(catalog.names, ["Castellers de la Vila de Gràcia", "Colla A"])
        XCTAssertEqual(catalog.keys, ["castellers de la vila de gracia", "colla a"])
    }
}
