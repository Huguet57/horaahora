import Foundation
import Observation
import CastellsDomain

@MainActor
@Observable
public final class ConversationListViewModel {
    public private(set) var conversations: [ChatConversationSummary] = []
    public var errorMessage: String?
    private let repository: any ChatRepository

    public init(repository: any ChatRepository) {
        self.repository = repository
    }

    public func reload() {
        do {
            conversations = try repository.listConversations()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func delete(_ id: UUID) {
        do {
            try repository.deleteConversation(id: id)
            reload()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func rename(_ id: UUID, title: String) {
        do {
            try repository.renameConversation(id: id, title: title)
            reload()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
