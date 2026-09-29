import Foundation

/// How a castell of a planned performance ends, as the Jurat of the Concurs reads it.
public enum ComparatorOutcome: String, Codable, CaseIterable, Sendable {
    case unloaded
    case loaded
    case attempt
    case dismantledAttempt

    var shortLabel: String {
        switch self {
        case .unloaded: "D"
        case .loaded: "C"
        case .attempt: "I"
        case .dismantledAttempt: "ID"
        }
    }

    var label: String {
        switch self {
        case .unloaded: "Descarregat"
        case .loaded: "Carregat"
        case .attempt: "Intent"
        case .dismantledAttempt: "Intent desmuntat"
        }
    }

    var isAchieved: Bool { self == .unloaded || self == .loaded }
}

/// A castell a colla might try in one round, with how it ends.
public struct PlannedCastell: Codable, Hashable, Sendable {
    public var notation: String
    public var outcome: ComparatorOutcome

    public init(notation: String, outcome: ComparatorOutcome) {
        self.notation = notation
        self.outcome = outcome
    }
}

/// One colla of a comparison and the castell it tries in each of the five rounds.
public struct ComparatorColla: Codable, Hashable, Identifiable, Sendable {
    public static let roundCount = 5

    public var id: UUID
    public var name: String
    /// What the column shows when there are three or four colles.
    public var shortName: String
    public var rounds: [PlannedCastell?]
    /// The ones the Jurat would give it, which only break ties. Using two rounds for a castell
    /// that counts adds its own, see `ComparatorScore.penalties`.
    public var penalties: Int

    public init(id: UUID = UUID(), name: String, shortName: String) {
        self.id = id
        self.name = name
        self.shortName = shortName
        rounds = Array(repeating: nil, count: Self.roundCount)
        penalties = 0
    }
}

/// A whole "what if": every colla of the comparison and its performance.
public struct ComparatorScenario: Codable, Hashable, Identifiable, Sendable {
    public var id: UUID
    public var colles: [ComparatorColla]
    /// Pinned in the Favorits section, on top of the rest.
    public var isFavorite: Bool
    /// What the user called it; without one, the list names it after who wins.
    public var name: String?

    public init(id: UUID = UUID(), colles: [ComparatorColla], isFavorite: Bool = false, name: String? = nil) {
        self.id = id
        self.colles = colles
        self.isFavorite = isFavorite
        self.name = name
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        colles = try container.decode([ComparatorColla].self, forKey: .colles)
        // Scenarios saved before favourites existed have no flag.
        isFavorite = try container.decodeIfPresent(Bool.self, forKey: .isFavorite) ?? false
        name = try container.decodeIfPresent(String.self, forKey: .name)
    }
}

/// Why a round adds nothing to the final score.
enum NotCountedReason: Equatable {
    case attempt
    /// The same castell counts from a better round.
    case repeated
    /// Only two carregats count in 2026.
    case loadedLimit
    case outsideTopThree

    var label: String {
        switch self {
        case .attempt: "intent"
        case .repeated: "repetit"
        case .loadedLimit: "3r carregat"
        case .outsideTopThree: "fora de les 3"
        }
    }
}

struct RoundScore: Equatable {
    enum Status: Equatable {
        case empty
        case counted
        case notCounted(NotCountedReason)
    }

    let points: Int
    let status: Status
}

struct ComparatorScore: Equatable {
    let total: Int
    let rounds: [RoundScore]
    /// The colla's own plus two for each counted castell that took two rounds.
    let penalties: Int
    /// The counted points from the best castell down, to break ties.
    let countedPoints: [Int]
}

/// What stops a colla from trying a castell in a round, from the Protocol de plaça.
enum ComparatorRestriction: Equatable {
    case alreadyUnloaded
    case triedTwice
    /// Another height of the same base already counts.
    case sameBase(String)
    /// In the last two rounds, with three castells done, only a castell better than a
    /// descarregat or a carregat to repeat is allowed.
    case noImprovement

    var label: String {
        switch self {
        case .alreadyUnloaded: "ja descarregat"
        case .triedTwice: "ja intentat 2 cops"
        case let .sameBase(notation): "mateixa base que \(notation)"
        case .noImprovement: "no millora"
        }
    }
}

struct ComparatorStanding: Equatable {
    enum TieBreak: Equatable {
        case penalties
        case bestCastell
        case secondCastell
    }

    let collaID: UUID
    let score: ComparatorScore
    /// What puts it above the next colla when both have the same points.
    let tieBreak: TieBreak?
}
