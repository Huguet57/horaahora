import Foundation

/// The rules of the Concurs that a comparison needs: the final score, the ranking with its
/// tie-breaks and the castells a colla may try in each round.
///
/// It follows the Normes bàsiques and the Protocol de plaça of 2024, the latest complete ones,
/// with the 2026 change that only two carregats count.
struct ComparatorRules {
    /// The heights of one base, which cannot count together (Protocol de plaça, IX).
    private static let sameBaseGroups: [[String]] = [
        ["Pde5", "Pde6", "Pde7f", "Pde8fm", "Pde9fmp"],
        ["2de6", "2de7", "2de8f", "2de9fm", "2de10fmp"],
        ["2de8sf", "2de9sm"],
        ["3de7", "3de8", "3de9f", "3de10fm"],
        ["3de7a", "3de8a", "3de9fa"],
        ["3de7s", "3de8s"],
        ["3de9sf", "3de10sm"],
        ["4de7", "4de8", "4de9f", "4de10fm"],
        ["4de7a", "4de8a", "4de9fa"],
        ["4de9sf", "4de10sm"],
        ["5de7", "5de8", "5de9f"],
        ["5de7a", "5de8a"],
        ["7de7", "7de8", "7de9f"],
        ["9de6", "9de7", "9de8", "9de9f"],
    ]

    let castells: [String: ScoreTableCastell]
    private let baseOf: [String: Int]

    init(table: ScoreTable) {
        castells = Dictionary(uniqueKeysWithValues: table.castells.map { ($0.notation, $0) })
        var baseOf: [String: Int] = [:]
        for (index, group) in Self.sameBaseGroups.enumerated() {
            for notation in group { baseOf[notation] = index }
        }
        self.baseOf = baseOf
    }

    func points(of castell: PlannedCastell) -> Int {
        guard let entry = castells[castell.notation] else { return 0 }
        switch castell.outcome {
        case .unloaded: return entry.unloaded
        case .loaded: return entry.loaded
        case .attempt, .dismantledAttempt: return 0
        }
    }

    // MARK: Score

    /// The three best constructions, with at most two carregats and each castell once.
    func score(_ colla: ComparatorColla) -> ComparatorScore {
        score(rounds: colla.rounds, ownPenalties: colla.penalties)
    }

    private func score(rounds: [PlannedCastell?], ownPenalties: Int = 0) -> ComparatorScore {
        var statuses: [RoundScore.Status] = rounds.map { castell in
            guard let castell else { return .empty }
            return castell.outcome.isAchieved ? .notCounted(.outsideTopThree) : .notCounted(.attempt)
        }

        // Each castell once, from its best round.
        var bestRound: [String: Int] = [:]
        for (index, castell) in rounds.enumerated() {
            guard let castell, castell.outcome.isAchieved else { continue }
            if let current = bestRound[castell.notation],
               points(of: rounds[current]!) >= points(of: castell) {
                statuses[index] = .notCounted(.repeated)
            } else {
                if let current = bestRound[castell.notation] {
                    statuses[current] = .notCounted(.repeated)
                }
                bestRound[castell.notation] = index
            }
        }

        let candidates = bestRound.values.sorted()
        var best: [Int] = []
        var bestTotal = -1
        for size in 1...max(1, min(3, candidates.count)) where !candidates.isEmpty {
            for group in combinations(of: candidates, size: size) {
                let loaded = group.filter { rounds[$0]?.outcome == .loaded }.count
                guard loaded <= 2 else { continue }
                let total = group.reduce(0) { $0 + points(of: rounds[$1]!) }
                if total > bestTotal {
                    bestTotal = total
                    best = group
                }
            }
        }

        let loadedCounted = best.filter { rounds[$0]?.outcome == .loaded }.count
        for index in candidates where !best.contains(index) {
            let isLoaded = rounds[index]?.outcome == .loaded
            statuses[index] = .notCounted(isLoaded && loadedCounted >= 2 ? .loadedLimit : .outsideTopThree)
        }
        for index in best { statuses[index] = .counted }

        // Using two rounds for a castell that counts is a double penalty.
        let twoRoundPenalties = best.reduce(0) { sum, index in
            let notation = rounds[index]!.notation
            let tries = rounds.filter { $0?.notation == notation }.count
            return sum + (tries >= 2 ? 2 : 0)
        }

        let roundScores = zip(rounds, statuses).map { castell, status in
            RoundScore(points: castell.map(points(of:)) ?? 0, status: status)
        }
        let counted = best.map { points(of: rounds[$0]!) }.sorted(by: >)
        return ComparatorScore(
            total: counted.reduce(0, +),
            rounds: roundScores,
            penalties: ownPenalties + twoRoundPenalties,
            countedPoints: counted
        )
    }

    private func combinations(of items: [Int], size: Int) -> [[Int]] {
        guard size > 0 else { return [[]] }
        guard items.count >= size else { return [] }
        var result: [[Int]] = []
        for (index, item) in items.enumerated() {
            for rest in combinations(of: Array(items[(index + 1)...]), size: size - 1) {
                result.append([item] + rest)
            }
        }
        return result
    }

    // MARK: Ranking

    /// From the first to the last: points, then fewer penalties, then the best castell and the
    /// second best.
    func ranking(_ colles: [ComparatorColla]) -> [ComparatorStanding] {
        let scored = colles.map { ($0.id, score($0)) }
        let sorted = scored.sorted { lhs, rhs in
            let (a, b) = (lhs.1, rhs.1)
            if a.total != b.total { return a.total > b.total }
            if a.penalties != b.penalties { return a.penalties < b.penalties }
            let bestA = a.countedPoints.first ?? 0, bestB = b.countedPoints.first ?? 0
            if bestA != bestB { return bestA > bestB }
            return (a.countedPoints.dropFirst().first ?? 0) > (b.countedPoints.dropFirst().first ?? 0)
        }
        return sorted.enumerated().map { index, entry in
            let next = index + 1 < sorted.count ? sorted[index + 1].1 : nil
            return ComparatorStanding(collaID: entry.0, score: entry.1, tieBreak: next.flatMap { tieBreak(entry.1, over: $0) })
        }
    }

    private func tieBreak(_ a: ComparatorScore, over b: ComparatorScore) -> ComparatorStanding.TieBreak? {
        guard a.total == b.total else { return nil }
        if a.penalties != b.penalties { return .penalties }
        if a.countedPoints.first != b.countedPoints.first { return .bestCastell }
        if a.countedPoints.dropFirst().first != b.countedPoints.dropFirst().first { return .secondCastell }
        return nil
    }

    // MARK: Allowed attempts

    /// Why the colla could not try `notation` in `round`, given what it did in the rounds
    /// before; `nil` when it can.
    func restriction(of notation: String, inRound round: Int, for colla: ComparatorColla) -> ComparatorRestriction? {
        let before = Array(colla.rounds.prefix(round))
        let tries = before.compactMap { $0 }.filter { $0.notation == notation }
        if tries.contains(where: { $0.outcome == .unloaded }) { return .alreadyUnloaded }
        if tries.count >= 2 { return .triedTwice }

        let scoreBefore = score(rounds: before)
        let counted = zip(before, scoreBefore.rounds)
            .compactMap { castell, score in score.status == .counted ? castell : nil }
        if let base = baseOf[notation],
           let conflict = counted.first(where: { $0.notation != notation && baseOf[$0.notation] == base }) {
            return .sameBase(conflict.notation)
        }

        if round >= 3 {
            let achieved = before.compactMap { $0 }.filter { $0.outcome.isAchieved }
            if achieved.count >= 3 {
                let loadedBefore = achieved.contains { $0.notation == notation && $0.outcome == .loaded }
                let unloadedPoints = achieved.filter { $0.outcome == .unloaded }
                    .compactMap { castells[$0.notation]?.unloaded }
                let candidate = castells[notation]?.unloaded ?? 0
                let improves = unloadedPoints.isEmpty || candidate > (unloadedPoints.min() ?? 0)
                if !loadedBefore && !improves { return .noImprovement }
            }
        }
        return nil
    }

    // MARK: Steps

    /// The castells sorted by the points they would score with `outcome`, from the fewest.
    func ladder(for outcome: ComparatorOutcome) -> [ScoreTableCastell] {
        castells.values.sorted { lhs, rhs in
            outcome == .loaded
                ? (lhs.loaded, lhs.unloaded, lhs.notation) < (rhs.loaded, rhs.unloaded, rhs.notation)
                : (lhs.unloaded, lhs.loaded, lhs.notation) < (rhs.unloaded, rhs.loaded, rhs.notation)
        }
    }

    /// The next castell up (`by > 0`) or down in points that the colla may try in that round,
    /// with the same outcome.
    func step(from castell: PlannedCastell, inRound round: Int, for colla: ComparatorColla, by direction: Int) -> PlannedCastell? {
        neighbours(of: castell, inRound: round, for: colla, count: 1, direction: direction).first
    }

    /// Up to `count` allowed neighbours, the closest first.
    func neighbours(of castell: PlannedCastell, inRound round: Int, for colla: ComparatorColla, count: Int, direction: Int) -> [PlannedCastell] {
        let ladder = ladder(for: castell.outcome)
        guard let index = ladder.firstIndex(where: { $0.notation == castell.notation }) else { return [] }
        let indices = direction > 0
            ? Array(ladder.indices.suffix(from: index + 1))
            : Array(ladder.indices.prefix(upTo: index).reversed())
        return indices.lazy
            .map { ladder[$0] }
            .filter { restriction(of: $0.notation, inRound: round, for: colla) == nil }
            .prefix(count)
            .map { PlannedCastell(notation: $0.notation, outcome: castell.outcome) }
    }
}
