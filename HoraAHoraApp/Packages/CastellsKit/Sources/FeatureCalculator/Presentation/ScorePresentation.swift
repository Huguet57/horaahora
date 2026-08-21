import CastellsDomain

struct ScorePresentation {
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

    let title: String
    let outcome: Outcome
    let focusNotation: String?
    let rows: [Row]

    init?(response: ChatResponse) {
        guard
            let source = response.presentation,
            source.type == "score_ranking"
        else { return nil }
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
}
