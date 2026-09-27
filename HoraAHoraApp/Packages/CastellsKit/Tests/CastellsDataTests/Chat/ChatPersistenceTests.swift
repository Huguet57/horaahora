import Foundation
import XCTest
import CastellsDomain
@testable import CastellsData

@MainActor
final class ChatPersistenceTests: XCTestCase {
    func testConversationPersistsCanBeRenamedAndDeleted() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = StubChatRemoteService()
        let repository = SwiftDataChatRepository(
            container: container,
            remoteService: remote,
            installationID: "test-installation"
        )

        let id = try repository.createConversation(title: "Primera conversa")
        _ = try await repository.send(message: "5d9f o 4d9fa?", in: id)
        let sentRequest = await remote.lastRequest
        XCTAssertEqual(sentRequest?.installationID, "test-installation")

        let reopened = SwiftDataChatRepository(
            container: container,
            remoteService: remote,
            installationID: "test-installation"
        )
        let conversation = try reopened.loadConversation(id: id)
        XCTAssertEqual(conversation.messages.map(\.role), [.user, .assistant])
        XCTAssertEqual(conversation.messages.last?.content, "Guanya 4de9fa.")

        try reopened.renameConversation(id: id, title: "Concurs")
        XCTAssertEqual(try reopened.listConversations().first?.title, "Concurs")

        try reopened.deleteConversation(id: id)
        XCTAssertTrue(try reopened.listConversations().isEmpty)
    }

    func testRequestsAreSharedOnlyWhenThePreferenceCoversTheConversation() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = StubChatRemoteService()
        let sharing = SharingPreferencesStub()
        let repository = SwiftDataChatRepository(
            container: container,
            remoteService: remote,
            installationID: "test-installation",
            sharing: sharing
        )
        let id = try repository.createConversation(title: "Concurs")
        let createdAt = try repository.loadConversation(id: id).createdAt

        sharing.shares = true
        _ = try await repository.send(message: "5d9f o 4d9fa?", in: id)
        let shared = await remote.lastRequest
        XCTAssertEqual(shared?.shareForImprovement, true)
        XCTAssertEqual(sharing.askedCreationDates, [createdAt])

        sharing.shares = false
        _ = try await repository.send(message: "I el 3d10fm?", in: id)
        let private_ = await remote.lastRequest
        XCTAssertEqual(private_?.shareForImprovement, false)
    }

    func testRequestsAreNotSharedWithoutSharingPreferences() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = StubChatRemoteService()
        let repository = SwiftDataChatRepository(
            container: container,
            remoteService: remote,
            installationID: "test-installation"
        )

        let id = try repository.createConversation(title: "Concurs")
        _ = try await repository.send(message: "5d9f o 4d9fa?", in: id)

        let request = await remote.lastRequest
        XCTAssertEqual(request?.shareForImprovement, false)
    }
}

@MainActor
private final class SharingPreferencesStub: ConversationSharingPreferences {
    var shares = false
    private(set) var askedCreationDates: [Date] = []

    var isEnabled: Bool { shares }
    var isNoticeAcknowledged: Bool { true }

    func setEnabled(_ enabled: Bool) { shares = enabled }
    func noticeWasShown() {}
    func acknowledgeNotice() {}

    func sharesConversation(createdAt: Date) -> Bool {
        askedCreationDates.append(createdAt)
        return shares
    }
}

private actor StubChatRemoteService: ChatRemoteService {
    private(set) var lastRequest: ChatRequest?

    func send(request: ChatRequest) async throws -> ChatResponse {
        lastRequest = request
        return ChatResponse(
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
