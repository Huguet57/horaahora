import Foundation

/// A run of castells of the same group.
struct ScoreTableSection: Identifiable, Equatable {
    var id: String { castells.first?.notation ?? "grup-\(group)" }

    let group: Int
    let castells: [ScoreTableCastell]
}

extension ScoreTable {
    /// From the castell worth the most to the one worth the least, descarregat first and then
    /// carregat, with a new section wherever the group changes.
    var sectionsByPoints: [ScoreTableSection] {
        let castells = castells.sorted {
            ($0.unloaded, $0.loaded) > ($1.unloaded, $1.loaded)
        }
        var sections: [ScoreTableSection] = []
        for castell in castells {
            if let last = sections.last, last.group == castell.group {
                sections[sections.count - 1] = ScoreTableSection(
                    group: last.group,
                    castells: last.castells + [castell]
                )
            } else {
                sections.append(ScoreTableSection(group: castell.group, castells: [castell]))
            }
        }
        return sections
    }

    /// The castells below `castell` in the table whose descarregat is worth more than its
    /// carregat: what beats loading it. Castells above obviously do, and a tie does not win.
    func notationsBelowWhoseUnloadedBeats(loadedOf castell: ScoreTableCastell) -> [String] {
        sectionsByPoints
            .flatMap(\.castells)
            .filter {
                ($0.unloaded, $0.loaded) < (castell.unloaded, castell.loaded)
                    && $0.unloaded > castell.loaded
            }
            .map(\.notation)
    }
}

