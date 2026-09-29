import XCTest
@testable import FeatureScoreTable

final class ComparatorRulesTests: XCTestCase {
    private var rules: ComparatorRules!

    override func setUpWithError() throws {
        rules = ComparatorRules(table: try ScoreTable.bundled())
    }

    private func colla(_ rounds: [PlannedCastell?], penalties: Int = 0) -> ComparatorColla {
        var colla = ComparatorColla(name: "Prova", shortName: "PRV")
        for (index, castell) in rounds.enumerated() {
            colla.rounds[index] = castell
        }
        colla.penalties = penalties
        return colla
    }

    private func d(_ notation: String) -> PlannedCastell { PlannedCastell(notation: notation, outcome: .unloaded) }
    private func c(_ notation: String) -> PlannedCastell { PlannedCastell(notation: notation, outcome: .loaded) }
    private func i(_ notation: String) -> PlannedCastell { PlannedCastell(notation: notation, outcome: .attempt) }

    // MARK: Scoring

    func testTheThreeBestConstructionsCount() {
        let score = rules.score(colla([d("3de10fm"), d("4de10fm"), c("2de9sm"), d("3de9f")]))

        XCTAssertEqual(score.total, 4_525 + 4_930 + 4_685)
        XCTAssertEqual(score.rounds[3].status, .notCounted(.outsideTopThree))
    }

    func testAtMostTwoLoadedCastellsCount() {
        let score = rules.score(colla([c("3de10fm"), c("4de10fm"), c("2de9sm"), d("3de9f")]))

        XCTAssertEqual(score.total, 4_095 + 4_685 + 1_910)
        XCTAssertEqual(score.rounds[0].status, .notCounted(.loadedLimit))
        XCTAssertEqual(score.rounds[3].status, .counted)
    }

    func testAttemptsTakeARoundButScoreNothing() {
        let score = rules.score(colla([i("3de10fm"), d("4de9f")]))

        XCTAssertEqual(score.total, 1_820)
        XCTAssertEqual(score.rounds[0].points, 0)
        XCTAssertEqual(score.rounds[0].status, .notCounted(.attempt))
    }

    func testACastellAchievedTwiceCountsOnlyOnce() {
        let score = rules.score(colla([c("3de9f"), d("3de9f"), d("4de8")]))

        XCTAssertEqual(score.total, 1_910 + 845)
        XCTAssertEqual(score.rounds[0].status, .notCounted(.repeated))
        // Using two rounds for the same castell is a double penalty.
        XCTAssertEqual(score.penalties, 2)
    }

    func testAnEmptyPerformanceScoresZero() {
        let score = rules.score(ComparatorColla(name: "Buida", shortName: "B"))

        XCTAssertEqual(score.total, 0)
        XCTAssertTrue(score.rounds.allSatisfy { $0.status == .empty })
    }

    // MARK: Ranking

    func testTheRankingGoesByPointsAndThenByPenalties() {
        let first = colla([d("3de9f")], penalties: 1)
        let second = colla([d("3de9f")], penalties: 0)
        let third = colla([d("4de9f")])

        let ranking = rules.ranking([first, second, third])

        XCTAssertEqual(ranking.map(\.collaID), [second.id, first.id, third.id])
        XCTAssertEqual(ranking[0].tieBreak, .penalties)
    }

    func testATieWithTheSamePenaltiesGoesToTheBestCastell() {
        let lowerBest = colla([d("2de6"), c("9de6")])  // 300 + 295 = 595
        let higherBest = colla([c("2de6"), c("3de7")])  // 250 + 345 = 595

        let ranking = rules.ranking([lowerBest, higherBest])

        XCTAssertEqual(ranking.map(\.collaID), [higherBest.id, lowerBest.id])
        XCTAssertEqual(ranking[0].tieBreak, .bestCastell)
        XCTAssertNil(rules.ranking([higherBest, colla([d("3de9f")])])[0].tieBreak)
    }

    // MARK: Allowed attempts

    func testACastellAlreadyUnloadedCannotBeTriedAgain() {
        let plan = colla([d("3de9f")])

        XCTAssertEqual(rules.restriction(of: "3de9f", inRound: 1, for: plan), .alreadyUnloaded)
    }

    func testACastellTriedTwiceCannotBeTriedAgain() {
        let plan = colla([i("3de10fm"), i("3de10fm")])

        XCTAssertEqual(rules.restriction(of: "3de10fm", inRound: 2, for: plan), .triedTwice)
    }

    func testALoadedCastellCanBeTriedAgain() {
        let plan = colla([c("3de9f")])

        XCTAssertNil(rules.restriction(of: "3de9f", inRound: 1, for: plan))
    }

    func testAnotherHeightOfTheSameBaseAsACountedCastellIsNotAllowed() {
        let plan = colla([d("3de9f")])

        XCTAssertEqual(rules.restriction(of: "3de10fm", inRound: 1, for: plan), .sameBase("3de9f"))
        // The versions without folre are a different base.
        XCTAssertNil(rules.restriction(of: "3de9sf", inRound: 1, for: plan))
    }

    func testOnlyEarlierRoundsRestrictALaterOne() {
        let plan = colla([nil, nil, d("3de9f")])

        XCTAssertNil(rules.restriction(of: "3de9f", inRound: 0, for: plan))
    }

    func testTheLastTwoRoundsNeedAnImprovementOnceThreeCastellsAreDone() {
        let plan = colla([d("3de9f"), d("4de9f"), d("2de8f")])

        XCTAssertEqual(rules.restriction(of: "5de7", inRound: 3, for: plan), .noImprovement)
        XCTAssertNil(rules.restriction(of: "3de8s", inRound: 3, for: plan))
        // With fewer than three castells done, any castell of the table is allowed.
        let short = colla([d("3de9f"), i("4de9f"), d("2de8f")])
        XCTAssertNil(rules.restriction(of: "4de8", inRound: 3, for: short))
    }

    func testTheLastTwoRoundsAllowRepeatingALoadedCastell() {
        let plan = colla([d("3de9f"), d("4de9f"), c("2de8f")])

        XCTAssertNil(rules.restriction(of: "2de8f", inRound: 3, for: plan))
    }

    // MARK: Steps

    func testStepsMoveToTheNeighbourInPointsAndSkipWhatIsNotAllowed() {
        let plan = colla([d("3de10fm"), d("9de9f"), d("4de9sf")])

        // Above 4de9sf (4.105) come 2de8sf (4.310) and then 3de10fm (4.525), already unloaded.
        XCTAssertEqual(rules.step(from: d("4de9sf"), inRound: 2, for: plan, by: 1)?.notation, "2de8sf")
        XCTAssertEqual(rules.step(from: d("2de8sf"), inRound: 2, for: plan, by: 1)?.notation, "4de10fm")
        XCTAssertEqual(rules.step(from: d("4de9sf"), inRound: 2, for: plan, by: -1)?.notation, "3de9fa")
    }

    func testStepsFollowTheCarregatPointsForALoadedCastell() {
        let plan = colla([])

        // Carregat: 3de9f 1.585, 5de8a 1.555, 4de9f 1.510.
        XCTAssertEqual(rules.step(from: c("5de8a"), inRound: 0, for: plan, by: 1)?.notation, "3de9f")
        XCTAssertEqual(rules.step(from: c("5de8a"), inRound: 0, for: plan, by: -1)?.notation, "4de9f")
    }

    func testTheTopOfTheTableHasNoStepUp() {
        XCTAssertNil(rules.step(from: d("3de10sm"), inRound: 0, for: colla([]), by: 1))
    }
}
