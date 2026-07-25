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
            TimelineView(.periodic(from: .now, by: 60)) { context in
                conversationList(relativeTo: context.date)
            }
            .navigationTitle("Calculadora")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { showNewConversation() } label: {
                        Label("Conversa nova", systemImage: "square.and.pencil")
                    }
                }
            }
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

    private func conversationList(relativeTo referenceDate: Date) -> some View {
        List(selection: $selectedDestination) {
            if model.conversations.isEmpty {
                ContentUnavailableView {
                    Label("Cap conversa", systemImage: "bubble.left.and.bubble.right")
                } description: {
                    Text("Crea una conversa per comparar castells i actuacions.")
                }
                .listRowBackground(Color.clear)
            }
            ForEach(model.conversations) { conversation in
                NavigationLink(value: CalculatorDestination.conversation(conversation.id)) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text(conversation.title).lineLimit(1)
                        Text(
                            ConversationAgeFormatter.string(
                                from: conversation.updatedAt,
                                relativeTo: referenceDate
                            )
                        )
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }
                }
                .swipeActions(edge: .trailing) {
                    Button(role: .destructive) { model.delete(conversation.id) } label: {
                        Label("Elimina", systemImage: "trash")
                    }
                    Button {
                        renameTarget = conversation
                        renameText = conversation.title
                    } label: {
                        Label("Canvia el nom", systemImage: "pencil")
                    }
                    .tint(.blue)
                }
            }
        }
    }

    private func showNewConversation() {
        selectedDestination = .newConversation
        preferredCompactColumn = .detail
    }
}

private enum CalculatorDestination: Hashable {
    case conversation(UUID)
    case newConversation
}
