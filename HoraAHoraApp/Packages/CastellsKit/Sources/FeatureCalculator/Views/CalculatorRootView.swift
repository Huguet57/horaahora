import SwiftUI
import CastellsDomain

public struct CalculatorRootView: View {
    private let repository: any ChatRepository
    @State private var model: ConversationListViewModel
    @State private var selectedDestination: CalculatorDestination?
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
                selection: $selectedDestination,
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
        .calculatorTabBarVisibility(isChatPresented: selectedDestination != nil)
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
        selectedDestination = .newConversation
        preferredCompactColumn = .detail
    }

    private func beginRenaming(_ conversation: ChatConversationSummary) {
        renameTarget = conversation
        renameText = conversation.title
    }
}
