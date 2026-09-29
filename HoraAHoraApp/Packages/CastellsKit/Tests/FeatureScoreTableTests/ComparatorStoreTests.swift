import XCTest
@testable import FeatureScoreTable

@MainActor
final class ComparatorStoreTests: XCTestCase {
    private static let suite = "ComparatorStoreTests"

    /// A store with nothing saved: one scenario with Vilafranca and the Colla Vella.
    private func makeStore() throws -> ComparatorStore {
        let defaults = try XCTUnwrap(UserDefaults(suiteName: Self.suite))
        defaults.removePersistentDomain(forName: Self.suite)
        return ComparatorStore(rules: ComparatorRules(table: try ScoreTable.bundled()), defaults: defaults)
    }

    func testAddingACollaOnlyChangesTheScenarioOnScreen() throws {
        let store = try makeStore()
        let first = store.current
        store.duplicateCurrent()

        store.addColla(KnownColla(name: "Colla Joves", shortName: "JOVES"))

        XCTAssertEqual(store.current.colles.map(\.shortName), ["VERDS", "VELLA", "JOVES"])
        XCTAssertEqual(store.scenarios.first { $0.id == first.id }?.colles.map(\.shortName), ["VERDS", "VELLA"])
    }

    func testChangingAndRemovingACollaOnlyChangesTheScenarioOnScreen() throws {
        let store = try makeStore()
        let first = store.current
        store.duplicateCurrent()
        let vella = try XCTUnwrap(store.current.colles.last)

        store.replaceColla(vella.id, with: KnownColla(name: "Colla Joves", shortName: "JOVES"))
        XCTAssertEqual(store.current.colles.map(\.shortName), ["VERDS", "JOVES"])

        store.removeColla(vella.id)
        XCTAssertEqual(store.current.colles.map(\.shortName), ["VERDS"])
        XCTAssertEqual(store.scenarios.first { $0.id == first.id }?.colles.map(\.shortName), ["VERDS", "VELLA"])
    }

    func testAFavouriteGoesToTheEndOfTheFavouritesOnTopAndBackToTheTopOfTheRest() throws {
        let store = try makeStore()
        let first = store.current
        store.duplicateCurrent()
        store.duplicateCurrent()
        let last = store.current

        store.toggleFavorite(last)
        XCTAssertEqual(store.favorites.map(\.id), [last.id])
        XCTAssertEqual(store.scenarios.first?.id, last.id)

        store.toggleFavorite(first)
        XCTAssertEqual(store.favorites.map(\.id), [last.id, first.id])

        store.toggleFavorite(last)
        XCTAssertEqual(store.favorites.map(\.id), [first.id])
        XCTAssertEqual(store.others.first?.id, last.id)
    }

    func testScenariosMoveWithinTheirSection() throws {
        let store = try makeStore()
        store.duplicateCurrent()
        store.duplicateCurrent()
        let ids = store.scenarios.map(\.id)

        store.moveScenarios(favorites: false, from: IndexSet(integer: 2), to: 0)

        XCTAssertEqual(store.scenarios.map(\.id), [ids[2], ids[0], ids[1]])
    }

    func testADuplicateIsNotAFavourite() throws {
        let store = try makeStore()
        let first = store.current
        store.toggleFavorite(first)

        store.duplicateCurrent()

        XCTAssertEqual(store.favorites.map(\.id), [first.id])
        XCTAssertEqual(store.others.map(\.id), [store.current.id])
    }

    func testScenariosSavedBeforeFavouritesAndNamesStillLoad() throws {
        let colla = ComparatorColla(name: "Vilafranca", shortName: "VIL")
        let json = """
        {"id":"\(UUID().uuidString)","colles":[\(String(data: try JSONEncoder().encode(colla), encoding: .utf8)!)]}
        """
        let scenario = try JSONDecoder().decode(ComparatorScenario.self, from: Data(json.utf8))

        XCTAssertFalse(scenario.isFavorite)
        XCTAssertNil(scenario.name)
        XCTAssertEqual(scenario.colles.map(\.shortName), ["VIL"])
    }

    func testAScenarioCanBeNamedAndTheNameCleared() throws {
        let store = try makeStore()
        let scenario = store.current

        store.rename(scenario, to: "  Si la Vella carrega  ")
        XCTAssertEqual(store.current.name, "Si la Vella carrega")

        store.rename(store.current, to: " ")
        XCTAssertNil(store.current.name)
    }

    func testADuplicateHasNoName() throws {
        let store = try makeStore()
        store.rename(store.current, to: "Pla A")

        store.duplicateCurrent()

        XCTAssertNil(store.current.name)
    }

    func testSavedCollesTakeTheCurrentShortNameOfTheirColla() throws {
        let defaults = try XCTUnwrap(UserDefaults(suiteName: Self.suite))
        defaults.removePersistentDomain(forName: Self.suite)
        let scenario = ComparatorScenario(colles: [
            ComparatorColla(name: "Vilafranca", shortName: "VIL"),
            ComparatorColla(name: "Els meus", shortName: "MEUS"),
        ])
        let stored = ["scenarios": [scenario]]
        var json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(stored)) as? [String: Any])
        json["currentID"] = scenario.id.uuidString
        defaults.set(try JSONSerialization.data(withJSONObject: json), forKey: "comparator.scenarios.v1")

        let store = ComparatorStore(rules: ComparatorRules(table: try ScoreTable.bundled()), defaults: defaults)

        XCTAssertEqual(store.current.colles.map(\.shortName), ["VERDS", "MEUS"])
    }
}
