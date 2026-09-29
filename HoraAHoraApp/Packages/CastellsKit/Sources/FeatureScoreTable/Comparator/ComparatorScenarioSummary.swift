import Foundation

/// A scenario in two parts: who wins and by how much, "VELLA +450", and a line per colla with
/// its castells, "VIL 3d10fm 4d10fm 9d9fc", leaving out the colles without any.
struct ComparatorScenarioSummary: Equatable {
    let title: String
    let lines: [String]
}

extension PlannedCastell {
    /// The castell as castellers write it: "de" becomes "d", and the result follows unless it
    /// is descarregat, "c" for carregat, "i" for intent and "id" for intent desmuntat.
    var shortNotation: String {
        let suffix = switch outcome {
        case .unloaded: ""
        case .loaded: "c"
        case .attempt: "i"
        case .dismantledAttempt: "id"
        }
        return notation.replacingOccurrences(of: "de", with: "d") + suffix
    }
}

extension ComparatorRules {
    func summary(of scenario: ComparatorScenario) -> ComparatorScenarioSummary {
        let ranking = ranking(scenario.colles)
        let title: String
        if let first = ranking.first, first.score.total > 0 {
            let margin = ranking.count > 1 ? first.score.total - ranking[1].score.total : first.score.total
            let winner = scenario.colles.first { $0.id == first.collaID }?.shortName ?? ""
            title = margin > 0 ? "\(winner) +\(formattedPoints(margin))" : "Empat"
        } else {
            title = "Sense castells"
        }
        let lines = scenario.colles.compactMap { colla -> String? in
            let castells = colla.rounds.compactMap { $0?.shortNotation }
            return castells.isEmpty ? nil : ([colla.shortName] + castells).joined(separator: " ")
        }
        return ComparatorScenarioSummary(title: title, lines: lines)
    }
}
