import Foundation
import Observation

/// A cell of the grid: one colla in one round.
struct ComparatorCell: Hashable, Identifiable {
    var id: String { "\(collaID)-\(round)" }
    let collaID: UUID
    let round: Int
}

/// A colla the comparison offers to pick, with the short name for narrow columns.
struct KnownColla: Hashable, Identifiable {
    var id: String { name }
    let name: String
    let shortName: String

    static let all: [KnownColla] = [
        KnownColla(name: "Vilafranca", shortName: "VERDS"),
        KnownColla(name: "Colla Vella", shortName: "VELLA"),
        KnownColla(name: "Colla Joves", shortName: "JOVES"),
        KnownColla(name: "Jove de Tarragona", shortName: "JOVE"),
        KnownColla(name: "Barcelona", shortName: "CDB"),
        KnownColla(name: "Capgrossos", shortName: "CAPS"),
        KnownColla(name: "Sabadell", shortName: "SAB"),
        KnownColla(name: "Xiquets de Tarragona", shortName: "XDT"),
        KnownColla(name: "Sant Pere i Sant Pau", shortName: "SPSP"),
        KnownColla(name: "Nens del Vendrell", shortName: "NENS"),
        KnownColla(name: "Sant Cugat", shortName: "SCG"),
        KnownColla(name: "Xiquets de Reus", shortName: "REUS"),
        KnownColla(name: "Gràcia", shortName: "GRÀC"),
        KnownColla(name: "Lleida", shortName: "LLEI"),
        KnownColla(name: "Moixiganguers", shortName: "MOIX"),
        KnownColla(name: "Sants", shortName: "SANTS"),
        KnownColla(name: "Terrassa", shortName: "TERR"),
    ]
}

/// The scenarios of the comparator, the one on screen and the cell being edited.
@MainActor
@Observable
final class ComparatorStore {
    static let maxColles = 4
    private static let storageKey = "comparator.scenarios.v1"

    let rules: ComparatorRules
    private(set) var scenarios: [ComparatorScenario] { didSet { save() } }
    private(set) var currentID: UUID? { didSet { save() } }
    var selection: ComparatorCell?

    @ObservationIgnored private let defaults: UserDefaults

    init(rules: ComparatorRules, defaults: UserDefaults = .standard) {
        self.rules = rules
        self.defaults = defaults
        if let data = defaults.data(forKey: Self.storageKey),
           let stored = try? JSONDecoder().decode(Stored.self, from: data),
           !Self.isUntouchedStart(stored.scenarios) {
            // Favourites first, as the list shows them, and the known colles with today's short
            // name, which may have changed since they were saved.
            let loaded = stored.scenarios.map(Self.refreshingShortNames)
            scenarios = loaded.filter(\.isFavorite) + loaded.filter { !$0.isFavorite }
            currentID = stored.scenarios.contains { $0.id == stored.currentID }
                ? stored.currentID
                : stored.scenarios.first?.id
        } else {
            scenarios = []
            currentID = nil
        }
    }

    /// Vilafranca and the Colla Vella, the colles of the first scenario.
    private static var firstColles: [ComparatorColla] {
        KnownColla.all.prefix(2).map { ComparatorColla(name: $0.name, shortName: $0.shortName) }
    }

    /// Whether the scenarios are just the one every comparator used to start with, as it was:
    /// the list now starts empty, and creating the first scenario gives the same one.
    private static func isUntouchedStart(_ scenarios: [ComparatorScenario]) -> Bool {
        guard scenarios.count == 1, let scenario = scenarios.first else { return false }
        return !scenario.isFavorite && scenario.name == nil
            && scenario.colles.map(\.name) == firstColles.map(\.name)
            && scenario.colles.allSatisfy { $0.penalties == 0 && $0.rounds.allSatisfy { $0 == nil } }
    }

    private static func refreshingShortNames(_ scenario: ComparatorScenario) -> ComparatorScenario {
        var scenario = scenario
        for index in scenario.colles.indices {
            if let known = KnownColla.all.first(where: { $0.name == scenario.colles[index].name }) {
                scenario.colles[index].shortName = known.shortName
            }
        }
        return scenario
    }

    // MARK: Scenarios

    /// The scenario whose grid is open, or opens next. Without scenarios, one without colles,
    /// which no screen shows.
    var current: ComparatorScenario {
        get { scenarios.first { $0.id == currentID } ?? scenarios.first ?? ComparatorScenario(colles: []) }
        set {
            guard let index = scenarios.firstIndex(where: { $0.id == newValue.id }) else { return }
            scenarios[index] = newValue
        }
    }

    func show(_ scenario: ComparatorScenario) {
        selection = nil
        currentID = scenario.id
    }

    /// Puts a copy right after `scenario`, or on top of the rest for a favourite: a copy is never
    /// a favourite itself, nor keeps the name.
    @discardableResult
    func duplicate(_ scenario: ComparatorScenario) -> ComparatorScenario {
        var copy = scenario
        copy.id = UUID()
        copy.isFavorite = false
        copy.name = nil
        let index = scenario.isFavorite
            ? favorites.count
            : (scenarios.firstIndex { $0.id == scenario.id }.map { $0 + 1 } ?? scenarios.count)
        scenarios.insert(copy, at: index)
        return copy
    }

    /// A blank name clears it.
    func rename(_ scenario: ComparatorScenario, to name: String) {
        guard let index = scenarios.firstIndex(where: { $0.id == scenario.id }) else { return }
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        scenarios[index].name = trimmed.isEmpty ? nil : trimmed
    }

    var favorites: [ComparatorScenario] { scenarios.filter(\.isFavorite) }
    var others: [ComparatorScenario] { scenarios.filter { !$0.isFavorite } }

    /// A new favourite goes last among the favourites; an old one, first among the rest. Both
    /// are the place right after the other favourites.
    func toggleFavorite(_ scenario: ComparatorScenario) {
        guard let index = scenarios.firstIndex(where: { $0.id == scenario.id }) else { return }
        var moved = scenarios.remove(at: index)
        moved.isFavorite.toggle()
        scenarios.insert(moved, at: favorites.count)
    }

    /// Reorders the favourites or the rest, as a list's `onMove` reports it.
    func moveScenarios(favorites inFavorites: Bool, from source: IndexSet, to destination: Int) {
        let group = inFavorites ? favorites : others
        let moving = source.map { group[$0] }
        var rest = group.enumerated().filter { !source.contains($0.offset) }.map(\.element)
        rest.insert(contentsOf: moving, at: destination - source.filter { $0 < destination }.count)
        scenarios = inFavorites ? rest + others : favorites + rest
    }

    func duplicateCurrent() {
        show(duplicate(current))
    }

    /// A scenario with the colles of the first one and every round empty, at the end.
    @discardableResult
    func addEmptyScenario() -> ComparatorScenario {
        var colles = scenarios.first?.colles ?? Self.firstColles
        for index in colles.indices {
            colles[index].rounds = Array(repeating: nil, count: ComparatorColla.roundCount)
            colles[index].penalties = 0
        }
        let scenario = ComparatorScenario(colles: colles)
        scenarios.append(scenario)
        return scenario
    }

    func delete(_ scenario: ComparatorScenario) {
        guard let index = scenarios.firstIndex(where: { $0.id == scenario.id }) else { return }
        scenarios.remove(at: index)
        if scenario.id == currentID {
            selection = nil
            currentID = scenarios.isEmpty ? nil : scenarios[min(index, scenarios.count - 1)].id
        }
    }

    /// Empties every round of the scenario on screen, keeping its colles.
    func clearCurrent() {
        selection = nil
        var scenario = current
        for index in scenario.colles.indices {
            scenario.colles[index].rounds = Array(repeating: nil, count: ComparatorColla.roundCount)
            scenario.colles[index].penalties = 0
        }
        current = scenario
    }

    // MARK: Colles

    func colla(_ id: UUID) -> ComparatorColla? {
        current.colles.first { $0.id == id }
    }

    // Colles belong to the scenario on screen: the others keep theirs.

    func addColla(_ known: KnownColla) {
        guard current.colles.count < Self.maxColles else { return }
        var scenario = current
        scenario.colles.append(ComparatorColla(name: known.name, shortName: known.shortName))
        current = scenario
    }

    func replaceColla(_ id: UUID, with known: KnownColla) {
        update(id) {
            $0.name = known.name
            $0.shortName = known.shortName
        }
    }

    func removeColla(_ id: UUID) {
        guard current.colles.count > 1 else { return }
        if selection?.collaID == id { selection = nil }
        var scenario = current
        scenario.colles.removeAll { $0.id == id }
        current = scenario
    }

    func changePenalties(of id: UUID, by delta: Int) {
        update(id) { $0.penalties = max(0, $0.penalties + delta) }
    }

    // MARK: Cells

    func castell(at cell: ComparatorCell) -> PlannedCastell? {
        colla(cell.collaID)?.rounds[cell.round]
    }

    func set(_ castell: PlannedCastell?, at cell: ComparatorCell) {
        update(cell.collaID) { $0.rounds[cell.round] = castell }
    }

    func step(_ cell: ComparatorCell, by direction: Int) {
        guard let colla = colla(cell.collaID), let castell = colla.rounds[cell.round],
              let next = rules.step(from: castell, inRound: cell.round, for: colla, by: direction)
        else { return }
        set(next, at: cell)
    }

    func setOutcome(_ outcome: ComparatorOutcome, at cell: ComparatorCell) {
        guard var castell = castell(at: cell) else { return }
        castell.outcome = outcome
        set(castell, at: cell)
    }

    /// Where the castell list opens for a cell: its own castell, else the rival's in that round,
    /// else the colla's own last one, else any castell of the comparison.
    func anchor(for cell: ComparatorCell) -> String {
        if let castell = castell(at: cell) { return castell.notation }
        let others = current.colles.filter { $0.id != cell.collaID }
        return others.compactMap({ $0.rounds[cell.round] }).first?.notation
            ?? colla(cell.collaID)?.rounds.prefix(cell.round).compactMap({ $0 }).last?.notation
            ?? current.colles.flatMap({ $0.rounds.compactMap { $0 } }).first?.notation
            ?? Self.defaultAnchor
    }

    private static let defaultAnchor = "3de9f"

    private func update(_ id: UUID, _ change: (inout ComparatorColla) -> Void) {
        var scenario = current
        guard let index = scenario.colles.firstIndex(where: { $0.id == id }) else { return }
        change(&scenario.colles[index])
        current = scenario
    }

    // MARK: Storage

    private struct Stored: Codable {
        let scenarios: [ComparatorScenario]
        let currentID: UUID?
    }

    private func save() {
        let stored = Stored(scenarios: scenarios, currentID: currentID)
        if let data = try? JSONEncoder().encode(stored) {
            defaults.set(data, forKey: Self.storageKey)
        }
    }
}

/// "4.525", as the Concurs writes points.
func formattedPoints(_ points: Int) -> String {
    let digits = String(abs(points))
    var grouped = ""
    for (index, digit) in digits.enumerated() {
        if index > 0 && (digits.count - index) % 3 == 0 { grouped.append(".") }
        grouped.append(digit)
    }
    return points < 0 ? "−" + grouped : grouped
}

func formattedMargin(_ margin: Int) -> String {
    margin > 0 ? "+" + formattedPoints(margin) : margin < 0 ? formattedPoints(margin) : "="
}
