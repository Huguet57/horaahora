import XCTest
@testable import FeatureScoreTable

final class ComparatorScenarioSummaryTests: XCTestCase {
    private var rules: ComparatorRules!

    override func setUpWithError() throws {
        rules = ComparatorRules(table: try ScoreTable.bundled())
    }

    private func colla(_ shortName: String, _ rounds: [PlannedCastell?]) -> ComparatorColla {
        var colla = ComparatorColla(name: shortName, shortName: shortName)
        for (index, castell) in rounds.enumerated() {
            colla.rounds[index] = castell
        }
        return colla
    }

    func testTheTitleIsWhoWinsAndByHowMuchAndEachLineListsAColla() {
        let scenario = ComparatorScenario(colles: [
            colla("VIL", [
                PlannedCastell(notation: "3de10fm", outcome: .unloaded),
                PlannedCastell(notation: "4de10fm", outcome: .unloaded),
                PlannedCastell(notation: "9de9f", outcome: .loaded),
            ]),
            colla("VELLA", [
                PlannedCastell(notation: "4de9sf", outcome: .unloaded),
                PlannedCastell(notation: "4de10fm", outcome: .unloaded),
                PlannedCastell(notation: "3de9sf", outcome: .loaded),
            ]),
        ])

        let summary = rules.summary(of: scenario)

        XCTAssertEqual(summary.title, "VELLA +450")
        XCTAssertEqual(summary.lines, ["VIL 3d10fm 4d10fm 9d9fc", "VELLA 4d9sf 4d10fm 3d9sfc"])
    }

    func testAttemptsReadAsInCastellerNotationAndCollesWithoutCastellsAreLeftOut() {
        let scenario = ComparatorScenario(colles: [
            colla("VIL", [
                PlannedCastell(notation: "3de10fm", outcome: .attempt),
                nil,
                PlannedCastell(notation: "Pde8fm", outcome: .dismantledAttempt),
            ]),
            colla("VELLA", []),
        ])

        let summary = rules.summary(of: scenario)

        XCTAssertEqual(summary.lines, ["VIL 3d10fmi Pd8fmid"])
    }

    func testATieAndAnEmptyScenarioSaySo() {
        let tie = ComparatorScenario(colles: [
            colla("VIL", [PlannedCastell(notation: "3de9f", outcome: .unloaded)]),
            colla("VELLA", [PlannedCastell(notation: "3de9f", outcome: .unloaded)]),
        ])
        let empty = ComparatorScenario(colles: [colla("VIL", []), colla("VELLA", [])])

        XCTAssertEqual(rules.summary(of: tie).title, "Empat")
        XCTAssertEqual(rules.summary(of: empty).title, "Sense castells")
    }
}
