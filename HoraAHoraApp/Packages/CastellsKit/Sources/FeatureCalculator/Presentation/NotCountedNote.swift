import CastellsDomain

/// One line under a calculation table saying which castells do not count and why.
/// Attempts are left out: their cell already reads «Intent».
enum NotCountedNote {
    static func text(for performances: [(label: String, castells: [ScoredCastellResponse])]) -> String? {
        let parts = performances.compactMap { performance -> (label: String, reasons: String, count: Int)? in
            reasons(for: performance.castells).map { (performance.label, $0.text, $0.count) }
        }
        guard !parts.isEmpty else { return nil }
        let lead = parts.map(\.count).reduce(0, +) == 1 ? "No compta" : "No compten"
        if performances.count == 1 { return "\(lead): \(parts[0].reasons)." }
        return "\(lead) — " + parts.map { "\($0.label): \($0.reasons)." }.joined(separator: " ")
    }

    private static func reasons(for castells: [ScoredCastellResponse]) -> (text: String, count: Int)? {
        var order: [String] = []
        var notations: [String: [String]] = [:]
        for castell in castells where !castell.counted {
            guard let reason = castell.reason.flatMap(label(for:)) else { continue }
            if notations[reason] == nil { order.append(reason) }
            notations[reason, default: []].append(castell.canonical ?? castell.input)
        }
        guard !order.isEmpty else { return nil }
        let text = order.map { "\(joined(notations[$0] ?? [])) (\($0))" }.joined(separator: ", ")
        return (text, notations.values.map(\.count).reduce(0, +))
    }

    private static func label(for reason: String) -> String? {
        switch reason {
        case "duplicate_structure": "repetit"
        case "loaded_limit": "només compten 2 carregats"
        case "outside_top_three": "fora de les 3 millors"
        default: nil
        }
    }

    private static func joined(_ items: [String]) -> String {
        guard let last = items.last, items.count > 1 else { return items.joined() }
        return items.dropLast().joined(separator: ", ") + " i " + last
    }
}
