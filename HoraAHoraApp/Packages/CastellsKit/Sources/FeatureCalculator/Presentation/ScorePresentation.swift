import CastellsDomain

struct ScorePresentation {
    enum Kind {
        case ranking
        case card
    }

    enum Outcome {
        case loaded
        case unloaded
        case both
    }

    struct Row: Identifiable {
        var id: Int { position }

        let position: Int
        let notation: String
        let loadedPoints: Int
        let unloadedPoints: Int
    }

    let kind: Kind
    let title: String
    let outcome: Outcome
    let focusNotation: String?
    let rows: [Row]

    var focusRow: Row? {
        guard let focusNotation else { return nil }
        return rows.first { $0.notation == focusNotation }
    }

    var previousRow: Row? {
        guard let focusIndex, focusIndex > rows.startIndex else { return nil }
        return rows[rows.index(before: focusIndex)]
    }

    var nextRow: Row? {
        guard let focusIndex else { return nil }
        let index = rows.index(after: focusIndex)
        return rows.indices.contains(index) ? rows[index] : nil
    }

    init?(response: ChatResponse) {
        guard let source = response.presentation else { return nil }
        switch source.type {
        case "score_ranking": kind = .ranking
        case "score_card": kind = .card
        default: return nil
        }
        switch source.outcome {
        case "loaded": outcome = .loaded
        case "unloaded": outcome = .unloaded
        case "both": outcome = .both
        default: return nil
        }
        title = source.title
        focusNotation = source.focusNotation
        rows = source.rows.map {
            Row(
                position: $0.position,
                notation: $0.notation,
                loadedPoints: $0.loadedPoints,
                unloadedPoints: $0.unloadedPoints
            )
        }
    }

    private var focusIndex: [Row].Index? {
        guard let focusNotation else { return nil }
        return rows.firstIndex { $0.notation == focusNotation }
    }
}
