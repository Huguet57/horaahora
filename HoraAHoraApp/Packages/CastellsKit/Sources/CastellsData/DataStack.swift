import SwiftData

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
