import Foundation
import SwiftData
import CastellsDomain

@MainActor
public final class SwiftDataChatRepository: ChatRepository {
    private let context: ModelContext
    private let remoteService: any ChatRemoteService

    public init(container: ModelContainer, remoteService: any ChatRemoteService) {
        self.context = ModelContext(container)
        self.remoteService = remoteService
    }

    public func listConversations() throws -> [ChatConversationSummary] {
        let records = try context.fetch(FetchDescriptor<ConversationRecord>(sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]))
        return records.map(Self.summary)
    }

    public func createConversation(title: String) throws -> UUID {
        let record = ConversationRecord(title: Self.cleanTitle(title))
        context.insert(record)
        try context.save()
        return record.id
    }

    public func loadConversation(id: UUID) throws -> ChatConversation {
        Self.thread(try record(id: id))
    }

    public func renameConversation(id: UUID, title: String) throws {
        let conversation = try record(id: id)
        conversation.title = Self.cleanTitle(title)
        conversation.updatedAt = .now
        try context.save()
    }

    public func deleteConversation(id: UUID) throws {
        context.delete(try record(id: id))
        try context.save()
    }

    public func send(message: String, in conversationID: UUID) async throws -> ChatConversation {
        let conversation = try record(id: conversationID)
        let userMessage = MessageRecord(
            roleRaw: ChatRole.user.rawValue,
            content: message.trimmingCharacters(in: .whitespacesAndNewlines),
            deliveryStateRaw: MessageDeliveryState.sending.rawValue,
            conversation: conversation
        )
        conversation.messages.append(userMessage)
        conversation.updatedAt = .now
        context.insert(userMessage)
        try context.save()
        return try await deliver(userMessage, in: conversation)
    }

    public func retry(messageID: UUID, in conversationID: UUID) async throws -> ChatConversation {
        let conversation = try record(id: conversationID)
        guard let message = conversation.messages.first(where: { $0.id == messageID && $0.roleRaw == ChatRole.user.rawValue }) else {
            throw RepositoryError.messageNotFound
        }
        message.deliveryStateRaw = MessageDeliveryState.sending.rawValue
        try context.save()
        return try await deliver(message, in: conversation)
    }

    private func deliver(_ userMessage: MessageRecord, in conversation: ConversationRecord) async throws -> ChatConversation {
        let ordered = conversation.messages.sorted { $0.createdAt < $1.createdAt }
        let request = ChatRequest(
            conversationID: conversation.id,
            installationID: InstallationIdentifier.current,
            messages: ordered.suffix(12).compactMap { message in
                guard let role = ChatRole(rawValue: message.roleRaw) else { return nil }
                return ChatRequestMessage(role: role, content: message.content)
            }
        )
        do {
            let response = try await remoteService.send(request: request)
            userMessage.deliveryStateRaw = MessageDeliveryState.sent.rawValue
            let assistant = MessageRecord(
                roleRaw: ChatRole.assistant.rawValue,
                content: response.reply,
                deliveryStateRaw: MessageDeliveryState.sent.rawValue,
                calculationData: try JSONEncoder.castellsAPI.encode(response),
                conversation: conversation
            )
            conversation.messages.append(assistant)
            conversation.updatedAt = .now
            context.insert(assistant)
            try context.save()
            return Self.thread(conversation)
        } catch {
            userMessage.deliveryStateRaw = MessageDeliveryState.failed.rawValue
            conversation.updatedAt = .now
            try? context.save()
            throw error
        }
    }

    private func record(id: UUID) throws -> ConversationRecord {
        let records = try context.fetch(FetchDescriptor<ConversationRecord>())
        guard let record = records.first(where: { $0.id == id }) else {
            throw RepositoryError.conversationNotFound
        }
        return record
    }

    private static func cleanTitle(_ title: String) -> String {
        let clean = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if clean.isEmpty { return "Conversa nova" }
        return String(clean.prefix(48))
    }

    private static func summary(_ record: ConversationRecord) -> ChatConversationSummary {
        ChatConversationSummary(id: record.id, title: record.title, createdAt: record.createdAt, updatedAt: record.updatedAt)
    }

    private static func thread(_ record: ConversationRecord) -> ChatConversation {
        let messages = record.messages
            .sorted { $0.createdAt < $1.createdAt }
            .compactMap { message -> ChatMessage? in
                guard
                    let role = ChatRole(rawValue: message.roleRaw),
                    let state = MessageDeliveryState(rawValue: message.deliveryStateRaw)
                else { return nil }
                let response = message.calculationData.flatMap { try? JSONDecoder.castellsAPI.decode(ChatResponse.self, from: $0) }
                return ChatMessage(
                    id: message.id,
                    role: role,
                    content: message.content,
                    createdAt: message.createdAt,
                    deliveryState: state,
                    calculation: response
                )
            }
        return ChatConversation(
            id: record.id,
            title: record.title,
            createdAt: record.createdAt,
            updatedAt: record.updatedAt,
            messages: messages
        )
    }
}

public enum RepositoryError: LocalizedError {
    case conversationNotFound
    case messageNotFound

    public var errorDescription: String? {
        switch self {
        case .conversationNotFound: "No s'ha trobat la conversa."
        case .messageNotFound: "No s'ha trobat el missatge."
        }
    }
}
