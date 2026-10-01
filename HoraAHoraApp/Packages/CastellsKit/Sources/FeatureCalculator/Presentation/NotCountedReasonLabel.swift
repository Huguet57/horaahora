import CastellsDomain

extension ScoredCastellResponse {
    /// Why an uncounted castell is left out, with the comparator's wording; nil when it counts.
    /// An attempt already reads «Intent», so it needs no extra label.
    var notCountedReason: String? {
        guard !counted else { return nil }
        switch reason {
        case "duplicate_structure": return "repetit"
        case "loaded_limit": return "3r carregat"
        case "outside_top_three": return "fora de les 3"
        default: return nil
        }
    }
}
