import XCTest
@testable import FeatureScoreTable

final class ScoreTableSectionsTests: XCTestCase {
    private var table: ScoreTable!

    override func setUpWithError() throws {
        table = try ScoreTable.bundled()
    }

    func testTheBundledTableHasEveryCastell() throws {
        XCTAssertEqual(table.castells.count, 47)
        let first = try XCTUnwrap(table.castells.first)
        XCTAssertEqual(first.notation, "2de6")
        XCTAssertEqual(first.name, "Torre de sis")
        XCTAssertEqual(first.group, 1)
        XCTAssertEqual(first.loaded, 250)
        XCTAssertEqual(first.unloaded, 300)
    }

    func testCastellsGoFromTheMostPointsToTheFewest() {
        let castells = table.sectionsByPoints.flatMap(\.castells)

        XCTAssertEqual(castells.count, 47)
        XCTAssertEqual(castells.first?.notation, "3de10sm")
        XCTAssertEqual(castells.last?.notation, "2de6")
        for (castell, next) in zip(castells, castells.dropFirst()) {
            XCTAssertGreaterThanOrEqual(castell.unloaded, next.unloaded, castell.notation)
        }
    }

    func testEachGroupIsOneSectionFromTheHighest() {
        let sections = table.sectionsByPoints

        XCTAssertEqual(sections.map(\.group), [7, 6, 5, 4, 3, 2, 1])
        XCTAssertEqual(sections.first?.castells.prefix(3).map(\.notation), ["3de10sm", "4de10sm", "2de10fmp"])
        XCTAssertEqual(Set(sections.map(\.id)).count, sections.count)
    }

    func testATappedCastellHighlightsTheCastellsBelowWhoseDescarregatBeatsItsCarregat() throws {
        let winners = table.notationsBelowWhoseUnloadedBeats(loadedOf: try castell("3de9fa"))

        XCTAssertEqual(winners, ["4de9fa", "5de9f"], "3.285 and 3.125 descarregat beat 3.100 carregat")
    }

    func testCastellsAboveAreLeftOutBecauseTheyObviouslyWin() throws {
        let winners = table.notationsBelowWhoseUnloadedBeats(loadedOf: try castell("3de9sf"))

        XCTAssertEqual(winners, ["Pde9fmp", "2de9sm", "9de9f"])
    }

    func testALowerCastellCanBeatTheCarregatOfAHigherOne() throws {
        XCTAssertEqual(
            table.notationsBelowWhoseUnloadedBeats(loadedOf: try castell("Pde8fm")),
            ["2de9fm", "3de8s", "9de8"]
        )
    }

    func testATieDoesNotWin() throws {
        let winners = table.notationsBelowWhoseUnloadedBeats(loadedOf: try castell("2de7"))

        XCTAssertEqual(winners, ["9de7", "3de7s"], "5de7a's 670 descarregat only ties 670 carregat")
    }

    private func castell(_ notation: String) throws -> ScoreTableCastell {
        try XCTUnwrap(table.castells.first { $0.notation == notation })
    }
}
