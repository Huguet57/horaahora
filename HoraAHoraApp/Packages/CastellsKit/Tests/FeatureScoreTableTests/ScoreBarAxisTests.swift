import CoreGraphics
import XCTest
@testable import FeatureScoreTable

final class ScoreBarAxisTests: XCTestCase {
    private let top = castell("3de10sm", loaded: 6_205, unloaded: 7_475)
    private let middle = castell("9de9f", loaded: 4_295, unloaded: 5_180)
    private let bottom = castell("5de9f", loaded: 2_595, unloaded: 3_125)
    private let below = castell("7de9f", loaded: 2_500, unloaded: 3_010)

    func testTheWindowFillsTheBarFromNearTheLeftToTheRight() throws {
        let axis = try XCTUnwrap(ScoreBarAxis(visible: [(top, 1), (middle, 1), (bottom, 1)]))

        XCTAssertEqual(axis.fraction(of: 7_475), 1)
        XCTAssertEqual(axis.fraction(of: 2_595), ScoreBarAxis.leadingFraction, accuracy: 0.000_1)
        XCTAssertLessThan(axis.fraction(of: 2_595), axis.fraction(of: 3_125))
    }

    func testAPartlyVisibleRowWeighsInProportion() throws {
        let whole = try XCTUnwrap(ScoreBarAxis(visible: [(top, 1), (middle, 1), (bottom, 1)]))
        let entering = try XCTUnwrap(ScoreBarAxis(visible: [(top, 1), (middle, 1), (bottom, 1), (below, 0.5)]))
        let inside = try XCTUnwrap(ScoreBarAxis(visible: [(top, 1), (middle, 1), (bottom, 1), (below, 1)]))

        XCTAssertLessThan(inside.lowerBound, entering.lowerBound)
        XCTAssertLessThan(entering.lowerBound, whole.lowerBound)
        XCTAssertEqual(entering.lowerBound, (whole.lowerBound + inside.lowerBound) / 2, accuracy: 0.001)
    }

    func testTheScaleDoesNotJumpWhenARowEntersOrLeaves() throws {
        let without = try XCTUnwrap(ScoreBarAxis(visible: [(middle, 1), (bottom, 1)]))
        let barelyIn = try XCTUnwrap(ScoreBarAxis(visible: [(top, 0.001), (middle, 1), (bottom, 1)]))
        let almostIn = try XCTUnwrap(ScoreBarAxis(visible: [(top, 0.999), (middle, 1), (bottom, 1)]))
        let with = try XCTUnwrap(ScoreBarAxis(visible: [(top, 1), (middle, 1), (bottom, 1)]))

        XCTAssertEqual(barelyIn.upperBound, without.upperBound, accuracy: 3)
        XCTAssertEqual(almostIn.upperBound, with.upperBound, accuracy: 3)
    }

    func testRowsOffScreenDoNotCount() throws {
        let axis = try XCTUnwrap(ScoreBarAxis(visible: [(top, 0), (middle, 1), (bottom, 1)]))

        XCTAssertEqual(axis.upperBound, 5_180)
        XCTAssertNil(ScoreBarAxis(visible: [(top, 0)]))
    }

    func testValuesOutsideTheWindowStayWithinTheBar() throws {
        let axis = try XCTUnwrap(ScoreBarAxis(visible: [(middle, 1), (bottom, 1)]))

        XCTAssertEqual(axis.fraction(of: 7_475), 1)
        XCTAssertEqual(axis.fraction(of: 250), 0)
    }

    func testTheWholeTableIsTheStartingScale() throws {
        let axis = ScoreBarAxis(castells: try ScoreTable.bundled().castells)

        XCTAssertEqual(axis.upperBound, 7_475)
        XCTAssertEqual(axis.fraction(of: 250), ScoreBarAxis.leadingFraction, accuracy: 0.000_1)
    }

    func testABarCountsWholeInsideTheWindowAndFadesOutsideIt() {
        let window: ClosedRange<CGFloat> = 200...700

        XCTAssertEqual(weight(at: 450, in: window), 1)
        XCTAssertEqual(weight(at: 200, in: window), 1)
        XCTAssertEqual(weight(at: 180, in: window), 0.5, accuracy: 0.001)
        XCTAssertEqual(weight(at: 150, in: window), 0)
        XCTAssertEqual(weight(at: 720, in: window), 0.5, accuracy: 0.001)
        XCTAssertEqual(weight(at: 800, in: window), 0)
    }

    private func weight(at y: CGFloat, in window: ClosedRange<CGFloat>) -> Double {
        ScoreBarAxis.weight(ofBarAt: y, in: window, fadeAbove: 40, fadeBelow: 40)
    }

    private static func castell(_ notation: String, loaded: Int, unloaded: Int) -> ScoreTableCastell {
        ScoreTableCastell(notation: notation, name: notation, group: 7, loaded: loaded, unloaded: unloaded)
    }
}
