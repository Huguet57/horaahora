import XCTest
@testable import FeatureScoreTable

@MainActor
final class ComparatorStoreTests: XCTestCase {
    private static let suite = "ComparatorStoreTests"

    private func makeDefaults() throws -> UserDefaults {
        let defaults = try XCTUnwrap(UserDefaults(suiteName: Self.suite))
        defaults.removePersistentDomain(forName: Self.suite)
        return defaults
    }

    private func makeEmptyStore(defaults: UserDefaults? = nil) throws -> ComparatorStore {
        ComparatorStore(rules: ComparatorRules(table: try ScoreTable.bundled()), defaults: try defaults ?? makeDefaults())
    }

    /// A store with its first scenario on screen: Vilafranca and the Colla Vella.
    private func makeStore() throws -> ComparatorStore {
        let store = try makeEmptyStore()
        store.show(store.addEmptyScenario())
        return store
    }

    func testWithNothingSavedThereAreNoScenarios() throws {
        let store = try makeEmptyStore()

        XCTAssertTrue(store.scenarios.isEmpty)
    }

    func testTheFirstScenarioComparesVilafrancaAndTheCollaVella() throws {
        let store = try makeEmptyStore()

        let scenario = store.addEmptyScenario()

        XCTAssertEqual(store.scenarios.map(\.id), [scenario.id])
        XCTAssertEqual(store.current.id, scenario.id)
        XCTAssertEqual(scenario.colles.map(\.shortName), ["VERDS", "VELLA"])
    }

    func testTheOnlyScenarioCanBeDeleted() throws {
        let defaults = try makeDefaults()
        let store = try makeEmptyStore(defaults: defaults)
        let scenario = store.addEmptyScenario()
        store.rename(scenario, to: "Pla A")

        store.delete(scenario)

        XCTAssertTrue(store.scenarios.isEmpty)
        XCTAssertTrue(try makeEmptyStore(defaults: defaults).scenarios.isEmpty)
    }

    func testAScenarioAfterDeletingThemAllIsTheOneOnScreen() throws {
        let store = try makeStore()
        store.delete(store.current)

        let scenario = store.addEmptyScenario()

        XCTAssertEqual(store.current.id, scenario.id)
    }

    func testTheUntouchedScenarioEveryComparatorStartedWithIsDropped() throws {
        let defaults = try makeDefaults()
        let scenario = ComparatorScenario(colles: [
            ComparatorColla(name: "Vilafranca", shortName: "VERDS"),
            ComparatorColla(name: "Colla Vella", shortName: "VELLA"),
        ])
        try save([scenario], in: defaults)

        XCTAssertTrue(try makeEmptyStore(defaults: defaults).scenarios.isEmpty)
    }

    func testAnOnlyScenarioWithACastellIsKept() throws {
        let defaults = try makeDefaults()
        var scenario = ComparatorScenario(colles: [
            ComparatorColla(name: "Vilafranca", shortName: "VERDS"),
            ComparatorColla(name: "Colla Vella", shortName: "VELLA"),
        ])
        scenario.colles[0].rounds[0] = PlannedCastell(notation: "3de9f", outcome: .unloaded)
        try save([scenario], in: defaults)

        XCTAssertEqual(try makeEmptyStore(defaults: defaults).scenarios.map(\.id), [scenario.id])
    }

    /// Saves the scenarios as the store does, the first one on screen.
    private func save(_ scenarios: [ComparatorScenario], in defaults: UserDefaults) throws {
        let stored = ["scenarios": scenarios]
        var json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(stored)) as? [String: Any])
        json["currentID"] = scenarios[0].id.uuidString
        defaults.set(try JSONSerialization.data(withJSONObject: json), forKey: "comparator.scenarios.v1")
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
        let defaults = try makeDefaults()
        let scenario = ComparatorScenario(colles: [
            ComparatorColla(name: "Vilafranca", shortName: "VIL"),
            ComparatorColla(name: "Els meus", shortName: "MEUS"),
        ])
        try save([scenario], in: defaults)

        let store = try makeEmptyStore(defaults: defaults)

        XCTAssertEqual(store.current.colles.map(\.shortName), ["VERDS", "MEUS"])
    }

    func testEveryCollaOfTheDirectoryCanBePickedAfterTheContestOnes() {
        XCTAssertEqual(KnownColla.all.count, 118)
        XCTAssertEqual(KnownColla.contest.count, 17)
        XCTAssertEqual(KnownColla.all.prefix(2).map(\.shortName), ["VERDS", "VELLA"])
        XCTAssertEqual(Set(KnownColla.all.map(\.name)).count, KnownColla.all.count)
        XCTAssertEqual(Set(KnownColla.all.map(\.shortName)).count, KnownColla.all.count)
        XCTAssertTrue(KnownColla.all.allSatisfy { $0.shortName.count <= 5 })
    }

    func testTheCollesMatchAnyOfTheirNamesIgnoringAccents() {
        XCTAssertEqual(KnownColla.matching("  "), KnownColla.all)
        XCTAssertEqual(
            KnownColla.matching("minyons").map(\.name),
            ["Minyons de l'Arboç", "Minyons de Terrassa", "Santa Cristina d'Aro"]
        )
        XCTAssertEqual(KnownColla.matching("castellers de terrassa").map(\.name), ["Terrassa"])
        XCTAssertEqual(KnownColla.matching("vila de gracia").map(\.name), ["Gràcia"])
        XCTAssertEqual(KnownColla.matching("BDN", in: KnownColla.others).map(\.name), ["Badalona"])
    }

    func testACollaTypedByEitherOfItsNamesIsTheKnownOne() {
        XCTAssertEqual(KnownColla.named(" castellers de badalona ")?.shortName, "BDN")
        XCTAssertEqual(KnownColla.named("Minyons de Terrassa")?.shortName, "MINY")
        XCTAssertNil(KnownColla.named("Minyons"))
    }
}
