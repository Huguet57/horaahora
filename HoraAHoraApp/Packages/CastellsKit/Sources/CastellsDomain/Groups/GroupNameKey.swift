import Foundation

public enum GroupNameKey {
    public static func normalize(_ name: String) -> String {
        let apostrophes = name
            .replacingOccurrences(of: "’", with: "'")
            .replacingOccurrences(of: "‘", with: "'")
            .replacingOccurrences(of: "ʼ", with: "'")
        return apostrophes.folding(
            options: [.caseInsensitive, .diacriticInsensitive, .widthInsensitive],
            locale: Locale(identifier: "ca_ES")
        ).split(whereSeparator: \.isWhitespace).joined(separator: " ")
    }
}
