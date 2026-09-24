import Foundation
import CastellsDomain

enum AgendaGroupNameNormalizer {
    static func key(for name: String) -> String {
        GroupNameKey.normalize(name)
    }

    static func merged(preferred: [String], fallback: [String]) -> [String] {
        var namesByKey: [String: String] = [:]
        for name in preferred + fallback {
            let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { continue }
            let normalizedKey = key(for: trimmed)
            if namesByKey[normalizedKey] == nil {
                namesByKey[normalizedKey] = trimmed
            }
        }
        return namesByKey.values.sorted(by: areInAscendingOrder)
    }

    private static func areInAscendingOrder(_ lhs: String, _ rhs: String) -> Bool {
        lhs.compare(
            rhs,
            options: [.caseInsensitive, .diacriticInsensitive],
            range: nil,
            locale: Locale(identifier: "ca_ES")
        ) == .orderedAscending
    }
}
