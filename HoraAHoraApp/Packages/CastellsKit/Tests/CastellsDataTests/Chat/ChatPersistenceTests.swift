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

    func testCompleteScenarioSurvivesHistoryWindowAndReopening() async throws {
        let container = try DataStack.makeModelContainer(inMemory: true)
        let remote = StubChatRemoteService()
        let repository = SwiftDataChatRepository(container: container, remoteService: remote, installationID: "test")
        let performances = [PerformanceResponse(label: "Vella", total: 100, castells: [
            ScoredCastellResponse(input: "3d10fm", canonical: "3de10fm", outcome: "loaded", points: 100, counted: true, reason: nil),
            ScoredCastellResponse(input: "4d9fa", canonical: "4de9fa", outcome: "loaded", points: 90, counted: true, reason: nil),
            ScoredCastellResponse(input: "5d9f", canonical: "5de9f", outcome: "loaded", points: 80, counted: false, reason: "loaded_limit"),
            ScoredCastellResponse(input: "4d8", canonical: "4de8", outcome: "unloaded", points: 70, counted: true, reason: nil),
            ScoredCastellResponse(input: "3d8", canonical: "3de8", outcome: "unloaded", points: 60, counted: false, reason: "outside_top_three"),
            ScoredCastellResponse(input: "9d9f", canonical: "9de9f", outcome: "attempt", points: 0, counted: false, reason: "attempt")
        ])]
        await remote.setPerformances(performances)
        let id = try repository.createConversation(title: "Llarga")
        _ = try await repository.send(message: "Escenari original", in: id)
        await remote.setPerformances([])
        for _ in 0..<6 { _ = try await repository.send(message: "Hola", in: id) }

        let reopened = SwiftDataChatRepository(container: container, remoteService: remote, installationID: "test")
        _ = try await reopened.send(message: "I si descarreguen el 5d9f?", in: id)
        let sentRequest = await remote.lastRequest
        let request = try XCTUnwrap(sentRequest)
        XCTAssertEqual(request.messages.count, 12)
        XCTAssertFalse(request.messages.contains { $0.content == "Escenari original" })
        XCTAssertEqual(request.scenario, performances.map(ScenarioPerformance.init))
        let encoded = try JSONSerialization.jsonObject(with: JSONEncoder.castellsAPI.encode(request)) as! [String: Any]
        let scenario = encoded["scenario"] as! [[String: Any]]
        XCTAssertEqual((scenario[0]["castells"] as! [[String: Any]]).count, 6)

        let replacement = [PerformanceResponse(label: "Nou", total: 0, castells: [performances[0].castells[0]])]
        await remote.setPerformances(replacement)
        _ = try await reopened.send(message: "Comencem de nou: 3d10fm carregat", in: id)
        _ = try await reopened.send(message: "I descarregat?", in: id)
        let replaced = await remote.lastRequest
        XCTAssertEqual(replaced?.scenario, replacement.map(ScenarioPerformance.init))
        let other = try reopened.createConversation(title: "Una altra")
        _ = try await reopened.send(message: "Hola", in: other)
        let fresh = await remote.lastRequest
        XCTAssertEqual(fresh?.scenario, [])
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
    private var performances: [PerformanceResponse] = []

    func setPerformances(_ value: [PerformanceResponse]) { performances = value }

    func send(request: ChatRequest) async throws -> ChatResponse {
        lastRequest = request
        return ChatResponse(
            reply: "Guanya 4de9fa.",
            intent: "comparison",
            performances: performances,
            winnerLabel: "4de9fa",
            warnings: [],
            rulesetVersion: "concurs-2026",
            needsClarification: false
        )
    }
}
