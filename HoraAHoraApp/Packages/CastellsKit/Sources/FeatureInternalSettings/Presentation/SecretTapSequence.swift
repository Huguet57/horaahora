import Foundation

/// Seven quick taps on the version in Ajustos show or hide the sections hidden by default.
struct SecretTapSequence {
    static let requiredTaps = 7
    /// A longer pause between two taps starts the sequence again.
    static let maximumPause: TimeInterval = 1.5

    private var count = 0
    private var lastTap: Date?

    /// Whether this tap completes the sequence.
    mutating func register(at date: Date) -> Bool {
        if let lastTap, date.timeIntervalSince(lastTap) <= Self.maximumPause {
            count += 1
        } else {
            count = 1
        }
        lastTap = date
        guard count == Self.requiredTaps else { return false }
        count = 0
        lastTap = nil
        return true
    }
}
