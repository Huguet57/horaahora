import SwiftUI
import CastellsDomain

public struct CalculatorRootView: View {
    private let repository: any ChatRepository
    @State private var model: ConversationListViewModel
    @State private var selectedDestination: CalculatorDestination?
    @State private var hidesTabBar = false
    @State private var preferredCompactColumn = NavigationSplitViewColumn.sidebar
    @State private var renameTarget: ChatConversationSummary?
    @State private var renameText = ""

    public init(repository: any ChatRepository) {
        self.repository = repository
        _model = State(initialValue: ConversationListViewModel(repository: repository))
    }

    public var body: some View {
        NavigationSplitView(preferredCompactColumn: $preferredCompactColumn) {
            ConversationSidebar(
                conversations: model.conversations,
                selection: Binding(get: { selectedDestination }, set: { select($0) }),
                onCreate: showNewConversation,
                onDelete: model.delete,
                onRename: beginRenaming
            )
        } detail: {
            switch selectedDestination {
            case let .conversation(id):
                ChatView(repository: repository, conversationID: id)
                    .id(selectedDestination)
                    .onDisappear { model.reload() }
            case .newConversation:
                ChatView(
                    repository: repository,
                    conversationID: nil,
                    onConversationCreated: { model.reload() }
                )
                    .id(selectedDestination)
                    .onDisappear { model.reload() }
            case nil:
                CalculatorWelcomeView { showNewConversation() }
            }
        }
        .calculatorTabBarVisibility(isChatPresented: hidesTabBar)
        .task { model.reload() }
        .alert(
            "Canvia el nom",
            isPresented: Binding(
                get: { renameTarget != nil },
                set: { if !$0 { renameTarget = nil } }
            )
        ) {
            TextField("Títol", text: $renameText)
            Button("Desa") {
                if let target = renameTarget { model.rename(target.id, title: renameText) }
                renameTarget = nil
            }
            Button("Cancel·la", role: .cancel) { renameTarget = nil }
        }
    }

    private func showNewConversation() {
        select(.newConversation)
    }

    private func select(_ destination: CalculatorDestination?) {
        guard let destination, selectedDestination == nil else {
            // Going back, or switching chats side by side.
            selectedDestination = destination
            hidesTabBar = destination != nil
            return
        }
        guard !hidesTabBar else { return }
        // Hide the tab bar one update before pushing the chat: when both change together, the
        // chat is laid out above the tab bar and its composer drops once the transition ends.
        hidesTabBar = true
        Task { @MainActor in
            await Task.yield()
            guard hidesTabBar, selectedDestination == nil else { return }
            selectedDestination = destination
            preferredCompactColumn = .detail
        }
    }

    private func beginRenaming(_ conversation: ChatConversationSummary) {
        renameTarget = conversation
        renameText = conversation.title
    }
}
