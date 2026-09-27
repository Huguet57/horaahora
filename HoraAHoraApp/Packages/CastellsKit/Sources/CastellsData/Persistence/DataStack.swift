import SwiftData

/// The local store of both apps. Its schema keeps the Hora a Hora and Agenda tables, which only
/// the internal app uses, so that the public app opens the store of the versions that had them,
/// with their conversations.
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
