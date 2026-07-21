import Foundation
import XCTest
import CastellsDomain
@testable import FeatureCalculator

@MainActor
final class ChatViewModelTests: XCTestCase {
    func testSendingShowsTheUserMessageImmediatelyAndHidesSuggestions() async throws {
        let repository = SuspendedChatRepository()
        let model = ChatViewModel(repository: repository, conversationID: nil)
        model.draft = "Què val el 5d9f?"

        let task = Task { await model.send() }
        while !repository.didStartSending {
            await Task.yield()
        }

        XCTAssertTrue(model.isSending)
        XCTAssertFalse(model.showsPromptSuggestions)
        XCTAssertEqual(model.displayedMessages.count, 1)
        XCTAssertEqual(model.displayedMessages.first?.role, .user)
        XCTAssertEqual(model.displayedMessages.first?.content, "Què val el 5d9f?")
        XCTAssertEqual(model.displayedMessages.first?.deliveryState, .sending)

        repository.finishSending()
        await task.value

        XCTAssertFalse(model.isSending)
        XCTAssertEqual(model.displayedMessages.map(\.role), [.user, .assistant])
    }
}

@MainActor
private final class SuspendedChatRepository: ChatRepository {
    private let conversationID = UUID()
    private var continuation: CheckedContinuation<ChatConversation, any Error>?
    private(set) var didStartSending = false

    func listConversations() throws -> [ChatConversationSummary] { [] }

    func createConversation(title: String) throws -> UUID { conversationID }

    func loadConversation(id: UUID) throws -> ChatConversation {
        emptyConversation
    }

    func renameConversation(id: UUID, title: String) throws {}

    func deleteConversation(id: UUID) throws {}

    func send(message: String, in conversationID: UUID) async throws -> ChatConversation {
        didStartSending = true
        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
        }
    }

    func retry(messageID: UUID, in conversationID: UUID) async throws -> ChatConversation {
        emptyConversation
    }

    func finishSending() {
        let now = Date()
        continuation?.resume(returning: ChatConversation(
            id: conversationID,
            title: "Què val el 5d9f?",
            createdAt: now,
            updatedAt: now,
            messages: [
                ChatMessage(
                    id: UUID(),
                    role: .user,
                    content: "Què val el 5d9f?",
                    createdAt: now,
                    deliveryState: .sent
                ),
                ChatMessage(
                    id: UUID(),
                    role: .assistant,
                    content: "Resposta",
                    createdAt: now,
                    deliveryState: .sent
                )
            ]
        ))
        continuation = nil
    }

    private var emptyConversation: ChatConversation {
        let now = Date()
        return ChatConversation(
            id: conversationID,
            title: "Conversa nova",
            createdAt: now,
            updatedAt: now,
            messages: []
        )
    }
}
