import Foundation

/// A castell of the official score table and its points.
public struct ScoreTableCastell: Decodable, Hashable, Identifiable, Sendable {
    public var id: String { notation }

    public let notation: String
    /// The notation read out in Catalan, for screen readers.
    public let name: String
    public let group: Int
    public let loaded: Int
    public let unloaded: Int
}

/// The official table of the Concurs de Castells 2026 that the app bundles.
///
/// `scripts/export_score_table.py` generates it from the backend CSV, which stays the only
/// source of the points.
public struct ScoreTable: Decodable, Sendable {
    public let castells: [ScoreTableCastell]

    public static func bundled() throws -> ScoreTable {
        guard let url = Bundle.module.url(forResource: "score-table-2026", withExtension: "json")
        else { throw CocoaError(.fileReadNoSuchFile) }
        return try JSONDecoder().decode(ScoreTable.self, from: Data(contentsOf: url))
    }
}
