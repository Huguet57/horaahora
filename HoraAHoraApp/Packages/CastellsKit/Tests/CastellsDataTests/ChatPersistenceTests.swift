import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class ChatPersistenceTests: XCTestCase {
    func testConversationPersistsCanBeRenamedAndDeleted() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = StubChatRemoteService()
        let repository = SwiftDataChatRepository(container: container, remoteService: remote)

        let id = try repository.createConversation(title: "Primera conversa")
        _ = try await repository.send(message: "5d9f o 4d9fa?", in: id)

        let reopened = SwiftDataChatRepository(container: container, remoteService: remote)
        let conversation = try reopened.loadConversation(id: id)
        XCTAssertEqual(conversation.messages.map(\.role), [.user, .assistant])
        XCTAssertEqual(conversation.messages.last?.content, "Guanya 4de9fa.")

        try reopened.renameConversation(id: id, title: "Concurs")
        XCTAssertEqual(try reopened.listConversations().first?.title, "Concurs")

        try reopened.deleteConversation(id: id)
        XCTAssertTrue(try reopened.listConversations().isEmpty)
    }
}

private struct StubChatRemoteService: ChatRemoteService {
    func send(request: ChatRequest) async throws -> ChatResponse {
        ChatResponse(
            reply: "Guanya 4de9fa.",
            intent: "comparison",
            performances: [],
            winnerLabel: "4de9fa",
            warnings: [],
            rulesetVersion: "concurs-2026",
            needsClarification: false
        )
    }
}
