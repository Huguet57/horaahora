import SwiftData

/// The app's local store: the calculator's conversations. The schema also keeps the legacy-only
/// Hora a Hora and Agenda entities (see Models.swift), so that an upgrade opens the store of the
/// versions that had them, with their conversations, without a migration.
@MainActor
public enum DataStack {
    public static func makeModelContainer(inMemory: Bool = false) throws -> ModelContainer {
        let schema = Schema([
            ConversationRecord.self,
            MessageRecord.self,
            HourByHourCacheRecord.self,
            AgendaCacheRecord.self,
        ])
        let configuration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: inMemory)
        return try ModelContainer(for: schema, configurations: [configuration])
    }
}
