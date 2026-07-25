import Foundation
import CastellsDomain

struct ComparisonPresentation {
    struct Castell: Identifiable {
        let id: Int
        let notation: String
        let result: String
        let points: Int
        let counted: Bool
    }

    struct Column: Identifiable {
        let id: Int
        let label: String
        let total: Int
        let castells: [Castell]
        let isWinner: Bool
    }

    let columns: [Column]
    let winnerLabel: String?
    let margin: Int?
    let summary: String
    let maximumCastellCount: Int

    init?(response: ChatResponse) {
        guard
            response.intent == "comparison",
            response.performances.count >= 2,
            !response.needsClarification
        else { return nil }

        let displayLabels = Self.displayLabels(for: response.performances)
        columns = response.performances.enumerated().map { columnIndex, performance in
            Column(
                id: columnIndex,
                label: displayLabels[columnIndex],
                total: performance.total,
                castells: performance.castells.enumerated().map { castellIndex, castell in
                    Castell(
                        id: castellIndex,
                        notation: castell.canonical ?? castell.input,
                        result: Self.resultLabel(castell.outcome),
                        points: castell.points,
                        counted: castell.counted
                    )
                },
                isWinner: performance.label == response.winnerLabel
            )
        }
        maximumCastellCount = columns.map(\.castells.count).max() ?? 0

        if let sourceWinner = response.winnerLabel,
           let winnerIndex = response.performances.firstIndex(where: { $0.label == sourceWinner }) {
            winnerLabel = displayLabels[winnerIndex]
        } else {
            winnerLabel = nil
        }

        if let winner = winnerLabel {
            let totals = response.performances.map(\.total).sorted(by: >)
            let winningMargin = totals[0] - totals[1]
            margin = winningMargin
            summary = "Guanya \(winner) per \(winningMargin.formatted(.number.grouping(.automatic))) punts."
        } else {
            margin = nil
            let total = response.performances.first?.total ?? 0
            summary = "Empat a \(total.formatted(.number.grouping(.automatic))) punts."
        }
    }

    private static func displayLabels(for performances: [PerformanceResponse]) -> [String] {
        guard performances.count >= 2 else { return performances.map(\.label) }
        let notationSets = performances.map { performance in
            Set(performance.castells.map { compact($0.input) })
        }
        let generic = performances.map { isGenericLabel($0.label, performance: $0) }
        var used = Set(
            performances.enumerated().compactMap { index, performance in
                generic[index] ? nil : compact(performance.label)
            }
        )
        var labels: [String?] = []
        for (index, performance) in performances.enumerated() {
            guard generic[index] else {
                labels.append(performance.label.trimmingCharacters(in: .whitespacesAndNewlines))
                continue
            }
            let otherNotations = notationSets.enumerated().reduce(into: Set<String>()) { result, item in
                if item.offset != index { result.formUnion(item.element) }
            }
            let distinctive = performance.castells.first {
                !otherNotations.contains(compact($0.input))
            }?.input.trimmingCharacters(in: .whitespacesAndNewlines)
            let proposed = distinctive.map { "Amb \($0)" }
            if let proposed, !used.contains(compact(proposed)) {
                labels.append(proposed)
                used.insert(compact(proposed))
            } else {
                labels.append(nil)
            }
        }

        let alphabet = Array("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for index in labels.indices where labels[index] == nil {
            var candidateIndex = index
            var fallback: String
            repeat {
                fallback = candidateIndex < alphabet.count
                    ? String(alphabet[candidateIndex])
                    : "A\(candidateIndex + 1)"
                candidateIndex += 1
            } while used.contains(compact(fallback))
            labels[index] = fallback
            used.insert(compact(fallback))
        }
        return labels.compactMap { $0 }
    }

    private static func isGenericLabel(
        _ label: String,
        performance: PerformanceResponse
    ) -> Bool {
        let normalized = compact(label)
        if normalized.count == 1, normalized.first?.isLetter == true { return true }
        let parts = normalized.split(separator: " ").map(String.init)
        let genericRoots = ["costat", "opció", "opcio", "actuació", "actuacio"]
        if parts.count == 2,
           genericRoots.contains(parts[0]),
           (Int(parts[1]) != nil || (parts[1].count == 1 && parts[1].first?.isLetter == true)) {
            return true
        }
        let compactWithoutSpaces = normalized.replacingOccurrences(of: " ", with: "")
        return performance.castells.contains { castell in
            compact(castell.input).replacingOccurrences(of: " ", with: "") == compactWithoutSpaces
                || compact(castell.canonical ?? "").replacingOccurrences(of: " ", with: "") == compactWithoutSpaces
        }
    }

    private static func compact(_ value: String) -> String {
        value.lowercased().split(whereSeparator: \.isWhitespace).joined(separator: " ")
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
