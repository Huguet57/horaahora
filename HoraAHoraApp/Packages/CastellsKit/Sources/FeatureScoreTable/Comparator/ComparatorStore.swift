import Foundation
import Observation

/// A cell of the grid: one colla in one round.
struct ComparatorCell: Hashable, Identifiable {
    var id: String { "\(collaID)-\(round)" }
    let collaID: UUID
    let round: Int
}

/// A colla the comparison offers to pick, with the short name for narrow columns and the name
/// in the CCCC directory, which the picker also searches.
struct KnownColla: Hashable, Identifiable {
    var id: String { name }
    let name: String
    let shortName: String
    let officialName: String

    init(name: String, shortName: String, officialName: String? = nil) {
        self.name = name
        self.shortName = shortName
        self.officialName = officialName ?? name
    }

    /// The colles of the Concurs de Castells 2026, first.
    static let contest: [KnownColla] = [
        KnownColla(name: "Vilafranca", shortName: "VERDS", officialName: "Castellers de Vilafranca"),
        KnownColla(name: "Colla Vella", shortName: "VELLA", officialName: "Colla Vella dels Xiquets de Valls"),
        KnownColla(name: "Colla Joves", shortName: "JOVES", officialName: "Colla Joves Xiquets de Valls"),
        KnownColla(name: "Jove de Tarragona", shortName: "JOVE", officialName: "Colla Jove Xiquets de Tarragona"),
        KnownColla(name: "Barcelona", shortName: "CDB", officialName: "Castellers de Barcelona"),
        KnownColla(name: "Capgrossos", shortName: "CAPS", officialName: "Capgrossos de Mataró"),
        KnownColla(name: "Sabadell", shortName: "SAB", officialName: "Castellers de Sabadell"),
        KnownColla(name: "Xiquets de Tarragona", shortName: "XDT"),
        KnownColla(name: "Sant Pere i Sant Pau", shortName: "SPSP", officialName: "Colla Castellera Sant Pere i Sant Pau"),
        KnownColla(name: "Nens del Vendrell", shortName: "NENS"),
        KnownColla(name: "Sant Cugat", shortName: "SCG", officialName: "Castellers de Sant Cugat"),
        KnownColla(name: "Xiquets de Reus", shortName: "REUS"),
        KnownColla(name: "Gràcia", shortName: "GRÀC", officialName: "Castellers de la Vila de Gràcia"),
        KnownColla(name: "Lleida", shortName: "LLEI", officialName: "Castellers de Lleida"),
        KnownColla(name: "Moixiganguers", shortName: "MOIX", officialName: "Moixiganguers d'Igualada"),
        KnownColla(name: "Sants", shortName: "SANTS", officialName: "Castellers de Sants"),
        KnownColla(name: "Terrassa", shortName: "TERR", officialName: "Castellers de Terrassa"),
    ]

    /// Every other colla of the CCCC directory (castellscat.cat, 2026-07-25), by name.
    static let others: [KnownColla] = [
        KnownColla(name: "Al·lots de Llevant", shortName: "ALLOT"),
        KnownColla(name: "Alt Maresme", shortName: "AMAR", officialName: "Colla Castellera de l'Alt Maresme i la Selva Marítima"),
        KnownColla(name: "Altafulla", shortName: "ALTA", officialName: "Castellers d'Altafulla"),
        KnownColla(name: "Andorra", shortName: "AND", officialName: "Castellers d'Andorra"),
        KnownColla(name: "Arreplegats", shortName: "ARREP", officialName: "Arreplegats de la Zona Universitària"),
        KnownColla(name: "Badalona", shortName: "BDN", officialName: "Castellers de Badalona"),
        KnownColla(name: "Baix Montseny", shortName: "BMONT", officialName: "Castellers del Baix Montseny"),
        KnownColla(name: "Berga", shortName: "BERGA", officialName: "Castellers de Berga"),
        KnownColla(name: "Bergants", shortName: "BRGNT", officialName: "Bergants del Campus de Terrassa"),
        KnownColla(name: "Berlín", shortName: "BERL", officialName: "Colla Castellera de Berlín"),
        KnownColla(name: "Bordegassos", shortName: "BORD", officialName: "Bordegassos de Vilanova"),
        KnownColla(name: "Boston", shortName: "BOST", officialName: "Castellers de Boston"),
        KnownColla(name: "Brivalls", shortName: "BRIV", officialName: "Brivalls de Cornudella"),
        KnownColla(name: "Brussel·les", shortName: "BRUS", officialName: "Mannekes de Brussel·les"),
        KnownColla(name: "Caldes", shortName: "CALD", officialName: "Castellers de Caldes de Montbui"),
        KnownColla(name: "Cambrils", shortName: "CAMB", officialName: "Xiquets de Cambrils"),
        KnownColla(name: "Castellar", shortName: "CTLR", officialName: "Castellers de Castellar del Vallès"),
        KnownColla(name: "Castelldefels", shortName: "CDF", officialName: "Castellers de Castelldefels"),
        KnownColla(name: "Cerdanya", shortName: "CDNYA", officialName: "Colla Castellera de Cerdanya"),
        KnownColla(name: "Cerdanyola", shortName: "CERD", officialName: "Castellers de Cerdanyola"),
        KnownColla(name: "Copenhagen", shortName: "CPH", officialName: "Xiquets de Copenhagen"),
        KnownColla(name: "Cornellà", shortName: "CORN", officialName: "Castellers de Cornellà"),
        KnownColla(name: "Cubelles", shortName: "CUB", officialName: "Castellers del Foix de Cubelles"),
        KnownColla(name: "Descargolats", shortName: "DESC", officialName: "Descargolats de l'EEBE"),
        KnownColla(name: "Edinburgh", shortName: "EDI", officialName: "Colla Castellera d’Edinburgh"),
        KnownColla(name: "Éire", shortName: "ÉIRE", officialName: "Castellers d’Éire"),
        KnownColla(name: "El Prat", shortName: "PRAT", officialName: "Castellers del Prat de Llobregat"),
        KnownColla(name: "Emboirats", shortName: "EMBO", officialName: "Emboirats de la Universitat de Vic"),
        KnownColla(name: "Encantats de Begues", shortName: "ENC", officialName: "Colla Castellera Els Encantats de Begues"),
        KnownColla(name: "Engrescats", shortName: "ENGR", officialName: "Engrescats de la URL"),
        KnownColla(name: "Esparreguera", shortName: "ESPAR", officialName: "Castellers d'Esparreguera"),
        KnownColla(name: "Esperxats", shortName: "ESPX", officialName: "Esperxats de l'Estany"),
        KnownColla(name: "Esplugues", shortName: "ESPL", officialName: "Castellers d'Esplugues"),
        KnownColla(name: "Esquerra de l'Eixample", shortName: "EIX", officialName: "Colla Castellera de l'Esquerra de l'Eixample"),
        KnownColla(name: "Estocolm", shortName: "ESTOC", officialName: "Castellers d'Estocolm"),
        KnownColla(name: "Figueres", shortName: "FIG", officialName: "Colla Castellera de Figueres"),
        KnownColla(name: "Gambirots", shortName: "GAMB", officialName: "Gambirots de la UIB"),
        KnownColla(name: "Ganàpies", shortName: "GANÀ", officialName: "Ganàpies de la UAB"),
        KnownColla(name: "Gavà", shortName: "GAVÀ", officialName: "Colla Castellera de Gavà"),
        KnownColla(name: "Grillats", shortName: "GRILL", officialName: "Grillats del Campus del Baix Llobregat"),
        KnownColla(name: "Jove de Barcelona", shortName: "JBCN", officialName: "Colla Castellera Jove de Barcelona"),
        KnownColla(name: "Jove de l'Hospitalet", shortName: "HOSP", officialName: "Colla Jove de l'Hospitalet"),
        KnownColla(name: "Jove de Sitges", shortName: "SITG", officialName: "Colla Jove de Castellers de Sitges"),
        KnownColla(name: "L'Adroc", shortName: "ADROC", officialName: "Castellers de l'Adroc"),
        KnownColla(name: "La Bisbal", shortName: "BISB", officialName: "Colla Castellera La Bisbal del Penedès"),
        KnownColla(name: "La Selva", shortName: "SELVA", officialName: "Castellers de la Selva"),
        KnownColla(name: "Laietans", shortName: "LAIE", officialName: "Laietans de Gramenet"),
        KnownColla(name: "Lausanne", shortName: "LAUS", officialName: "Castellers de Lausanne"),
        KnownColla(name: "Les Roquetes", shortName: "ROQ", officialName: "Castellers de les Roquetes"),
        KnownColla(name: "Lluçanès", shortName: "LLUÇ", officialName: "Castellers del Lluçanès"),
        KnownColla(name: "Llunàtics", shortName: "LLUN", officialName: "Llunàtics UPC Vilanova"),
        KnownColla(name: "Lo Prado", shortName: "PRADO", officialName: "Castellers de Lo Prado"),
        KnownColla(name: "Londres", shortName: "LON", officialName: "Castellers of London"),
        KnownColla(name: "Madrid", shortName: "MAD", officialName: "Colla Castellera de Madrid"),
        KnownColla(name: "Mallorca", shortName: "MALL", officialName: "Castellers de Mallorca"),
        KnownColla(name: "Manyacs", shortName: "MANY", officialName: "Manyacs de Parets"),
        KnownColla(name: "Margeners", shortName: "MARG", officialName: "Margeners de Guissona"),
        KnownColla(name: "Marrecs", shortName: "MARR", officialName: "Marrecs de Salt"),
        KnownColla(name: "Matossers", shortName: "MATOS", officialName: "Matossers de Molins de Rei"),
        KnownColla(name: "Mediona", shortName: "MED", officialName: "Castellers de Mediona"),
        KnownColla(name: "Minyons de l'Arboç", shortName: "ARBOÇ"),
        KnownColla(name: "Minyons de Terrassa", shortName: "MINY"),
        KnownColla(name: "Mollet", shortName: "MOLL", officialName: "Castellers de Mollet"),
        KnownColla(name: "Montcada", shortName: "MONTC", officialName: "Castellers de Montcada i Reixac"),
        KnownColla(name: "Montreal", shortName: "MTL", officialName: "Castellers de Montreal"),
        KnownColla(name: "Nois de la Torre", shortName: "NOIS"),
        KnownColla(name: "Pallagos", shortName: "CONFL", officialName: "Pallagos del Conflent"),
        KnownColla(name: "Pallars", shortName: "PALL", officialName: "Castellers del Pallars"),
        KnownColla(name: "París", shortName: "PARÍS", officialName: "Castellers de París"),
        KnownColla(name: "Passerells", shortName: "PASS", officialName: "Passerells del TCM"),
        KnownColla(name: "Pataquers", shortName: "PATA", officialName: "Pataquers de la URV"),
        KnownColla(name: "Penjats", shortName: "PENJ", officialName: "Penjats del Campus de Manresa"),
        KnownColla(name: "Poble-sec", shortName: "PSEC", officialName: "Castellers del Poble Sec"),
        KnownColla(name: "Riberal", shortName: "RIB", officialName: "Castellers del Riberal"),
        KnownColla(name: "Rubí", shortName: "RUBÍ", officialName: "Castellers de Rubí"),
        KnownColla(name: "Sagals d'Osona", shortName: "SAGAL"),
        KnownColla(name: "Sagrada Família", shortName: "SGF", officialName: "Castellers de la Sagrada Família"),
        KnownColla(name: "Salats", shortName: "SALAT", officialName: "Salats de Súria"),
        KnownColla(name: "Sant Adrià", shortName: "SADR", officialName: "Castellers de Sant Adrià"),
        KnownColla(name: "Sant Feliu", shortName: "SFEL", officialName: "Castellers de Sant Feliu"),
        KnownColla(name: "Sant Vicenç", shortName: "SVIC", officialName: "Castellers de Sant Vicenç dels Horts"),
        KnownColla(name: "Santa Coloma", shortName: "SCOL", officialName: "Castellers de Santa Coloma"),
        KnownColla(name: "Santa Cristina d'Aro", shortName: "STCR", officialName: "Minyons de Santa Cristina d'Aro"),
        KnownColla(name: "Santpedor", shortName: "SPED", officialName: "Castellers de Santpedor"),
        KnownColla(name: "Sarrià", shortName: "SARR", officialName: "Castellers de Sarrià"),
        KnownColla(name: "Serrallo", shortName: "SERR", officialName: "Xiquets del Serrallo"),
        KnownColla(name: "Sydney", shortName: "SYD", officialName: "Castellers de Sydney"),
        KnownColla(name: "Tirallongues", shortName: "TIRA", officialName: "Tirallongues de Manresa"),
        KnownColla(name: "Torraires", shortName: "TORRA", officialName: "Torraires de Montblanc"),
        KnownColla(name: "Tortosa", shortName: "TORT", officialName: "Castellers de Tortosa"),
        KnownColla(name: "Trempats", shortName: "TREMP", officialName: "Trempats de la UPF"),
        KnownColla(name: "Vacarisses", shortName: "VAC", officialName: "Colla Castellera de Vacarisses"),
        KnownColla(name: "Vailets", shortName: "VAIL", officialName: "Vailets de Gelida"),
        KnownColla(name: "Vila-seca", shortName: "VSECA", officialName: "Xiquets de Vila-seca"),
        KnownColla(name: "Viladecans", shortName: "VLDC", officialName: "Castellers de Viladecans"),
        KnownColla(name: "Xerrics", shortName: "OLOT", officialName: "Xerrics d'Olot"),
        KnownColla(name: "Xicots", shortName: "XICOT", officialName: "Xicots de Vilafranca"),
        KnownColla(name: "Xics de Granollers", shortName: "GRAN"),
        KnownColla(name: "Xiqüelos del Delta", shortName: "DELTA", officialName: "Xiqüelos i Xiqüeles del Delta"),
        KnownColla(name: "Xoriguers", shortName: "XORI", officialName: "Xoriguers de la UdG"),
        KnownColla(name: "Zürich", shortName: "ZÜR", officialName: "Castellers de Zürich"),
    ]

    static let all = contest + others

    /// The colles whose name, short name or name in the directory contains `query`, ignoring
    /// case and accents; all of them without a query.
    static func matching(_ query: String, in colles: [KnownColla] = all) -> [KnownColla] {
        let query = query.trimmingCharacters(in: .whitespaces)
        guard !query.isEmpty else { return colles }
        return colles.filter { known in
            [known.name, known.shortName, known.officialName].contains { $0.localizedStandardContains(query) }
        }
    }

    /// The colla called `name`, by either of its names, ignoring case and accents.
    static func named(_ name: String) -> KnownColla? {
        let name = name.trimmingCharacters(in: .whitespaces)
        return all.first { known in
            [known.name, known.officialName].contains {
                $0.compare(name, options: [.caseInsensitive, .diacriticInsensitive]) == .orderedSame
            }
        }
    }
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
