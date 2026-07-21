import Foundation

@MainActor
public protocol HourByHourRepository: AnyObject {
    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage
}

@MainActor
public protocol AgendaRepository: AnyObject {
    var officialURL: URL { get }
    func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage
}

@MainActor
public protocol ChatRepository: AnyObject {
    func listConversations() throws -> [ChatConversationSummary]
    func createConversation(title: String) throws -> UUID
    func loadConversation(id: UUID) throws -> ChatConversation
    func renameConversation(id: UUID, title: String) throws
    func deleteConversation(id: UUID) throws
    func send(message: String, in conversationID: UUID) async throws -> ChatConversation
    func retry(messageID: UUID, in conversationID: UUID) async throws -> ChatConversation
}
