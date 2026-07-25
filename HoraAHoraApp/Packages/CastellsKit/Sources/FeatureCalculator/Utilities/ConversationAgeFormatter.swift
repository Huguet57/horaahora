import Foundation

enum ConversationAgeFormatter {
    static func string(from date: Date, relativeTo referenceDate: Date) -> String {
        let elapsedSeconds = max(0, Int(referenceDate.timeIntervalSince(date)))
        guard elapsedSeconds >= 60 else { return "menys d’1 min" }

        let days = elapsedSeconds / 86_400
        let hours = elapsedSeconds / 3_600 % 24
        let minutes = elapsedSeconds / 60 % 60
        var components: [String] = []
        if days > 0 { components.append(days == 1 ? "1 dia" : "\(days) dies") }
        if hours > 0 { components.append("\(hours) h") }
        if minutes > 0 { components.append("\(minutes) min") }
        return components.prefix(2).joined(separator: " i ")
    }
}
