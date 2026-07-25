import XCTest
@testable import FeatureAgenda

final class AgendaGroupNameNormalizerTests: XCTestCase {
    func testKeysIgnoreCaseAccentsWhitespaceAndApostropheVariants() {
        XCTAssertEqual(
            AgendaGroupNameNormalizer.key(for: "  Castellers   d’Àltafulla "),
            AgendaGroupNameNormalizer.key(for: "castellers d'altafulla")
        )
    }
}
