import Foundation
import Observation
import CastellsDomain

@MainActor
@Observable
public final class ChatViewModel {
    typealias Sleep = @MainActor @Sendable (Duration) async throws -> Void

    public var draft = ""
    public private(set) var conversation: ChatConversation?
    public private(set) var pendingUserMessage: ChatMessage?
    public private(set) var isSending = false
    public var errorMessage: String?
    public private(set) var showsSharingNotice: Bool
    private var conversationID: UUID?
    private let repository: any ChatRepository
    private let sharing: (any ConversationSharingPreferences)?
    private let sleep: Sleep
    private let onConversationCreated: @MainActor () -> Void

    public convenience init(
        repository: any ChatRepository,
        conversationID: UUID?,
        sharing: (any ConversationSharingPreferences)? = nil,
        onConversationCreated: @escaping @MainActor () -> Void = {}
    ) {
        self.init(
            repository: repository,
            conversationID: conversationID,
            sharing: sharing,
            sleep: { duration in try await ContinuousClock().sleep(for: duration) },
            onConversationCreated: onConversationCreated
        )
    }

    init(
        repository: any ChatRepository,
        conversationID: UUID?,
        sharing: (any ConversationSharingPreferences)? = nil,
        sleep: @escaping Sleep,
        onConversationCreated: @escaping @MainActor () -> Void = {}
    ) {
        self.repository = repository
        self.conversationID = conversationID
        self.sharing = sharing
        self.sleep = sleep
        self.onConversationCreated = onConversationCreated
        showsSharingNotice = sharing.map { $0.isEnabled && !$0.isNoticeAcknowledged } ?? false
    }

    public var displayedMessages: [ChatMessage] {
        (conversation?.messages ?? []) + [pendingUserMessage].compactMap { $0 }
    }

    public var showsPromptSuggestions: Bool {
        displayedMessages.isEmpty && !isSending
    }

    public func load() {
        guard let conversationID else { return }
        do {
            conversation = try repository.loadConversation(id: conversationID)
            isSending = conversation?.messages.contains { message in
                message.role == .user && message.deliveryState == .sending
            } ?? false
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func loadFollowingPendingResponse() async {
        load()
        while isSending && !Task.isCancelled {
            do {
                try await sleep(.milliseconds(250))
            } catch {
                return
            }
            guard !Task.isCancelled else { return }
            load()
        }
    }

    public func send() async {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        draft = ""
        pendingUserMessage = ChatMessage(
            id: UUID(),
            role: .user,
            content: text,
            createdAt: .now,
            deliveryState: .sending
        )
        isSending = true
        errorMessage = nil
        do {
            let id: UUID
            if let conversationID {
                id = conversationID
            } else {
                id = try repository.createConversation(title: text)
                conversationID = id
                onConversationCreated()
            }
            let updatedConversation = try await repository.send(message: text, in: id)
            pendingUserMessage = nil
            conversation = updatedConversation
        } catch {
            pendingUserMessage = nil
            errorMessage = error.localizedDescription
            load()
        }
        isSending = false
    }

    /// Sharing only starts once the notice has been on screen.
    public func sharingNoticeAppeared() {
        sharing?.noticeWasShown()
    }

    public func acceptSharing() {
        sharing?.acknowledgeNotice()
        showsSharingNotice = false
    }

    public func declineSharing() {
        sharing?.setEnabled(false)
        sharing?.acknowledgeNotice()
        showsSharingNotice = false
    }

    public func retry(_ messageID: UUID) async {
        guard let conversationID, !isSending else { return }
        isSending = true
        errorMessage = nil
        do {
            conversation = try await repository.retry(messageID: messageID, in: conversationID)
        } catch {
            errorMessage = error.localizedDescription
            load()
        }
        isSending = false
    }
}
