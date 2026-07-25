import Foundation

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
