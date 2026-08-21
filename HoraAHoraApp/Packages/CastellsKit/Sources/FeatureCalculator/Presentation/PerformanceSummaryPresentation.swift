import CastellsDomain

struct PerformanceSummaryPresentation {
    struct Row: Identifiable {
        let id: Int
        let notation: String
        let result: String
        let points: Int
        let counted: Bool
    }

    let title: String
    let rows: [Row]
    let total: Int

    init?(response: ChatResponse) {
        guard
            ["lookup", "total"].contains(response.intent),
            response.performances.count == 1,
            let performance = response.performances.first,
            !response.needsClarification
        else { return nil }

        title = response.intent == "lookup" ? "Puntuació" : "Actuació calculada"
        rows = performance.castells.enumerated().map { index, castell in
            Row(
                id: index,
                notation: castell.canonical ?? castell.input,
                result: Self.resultLabel(castell.outcome),
                points: castell.points,
                counted: castell.counted
            )
        }
        total = performance.total
    }

    private static func resultLabel(_ outcome: String) -> String {
        switch outcome {
        case "loaded": "Carregat"
        case "unloaded": "Descarregat"
        case "attempt": "Intent"
        default: outcome.capitalized
        }
    }
}
