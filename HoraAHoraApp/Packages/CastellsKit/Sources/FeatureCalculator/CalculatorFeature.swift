import Foundation
import Observation
import SwiftUI
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

public struct CalculatorRootView: View {
    private let repository: any ChatRepository
    @State private var model: ConversationListViewModel
    @State private var selectedID: UUID?
    @State private var showingNewConversation = false
    @State private var renameTarget: ChatConversationSummary?
    @State private var renameText = ""

    public init(repository: any ChatRepository) {
        self.repository = repository
        _model = State(initialValue: ConversationListViewModel(repository: repository))
    }

    public var body: some View {
        NavigationSplitView {
            List(selection: $selectedID) {
                if model.conversations.isEmpty {
                    ContentUnavailableView {
                        Label("Cap conversa", systemImage: "bubble.left.and.bubble.right")
                    } description: {
                        Text("Crea una conversa per comparar castells i actuacions.")
                    }
                    .listRowBackground(Color.clear)
                }
                ForEach(model.conversations) { conversation in
                    NavigationLink(value: conversation.id) {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(conversation.title).lineLimit(1)
                            Text(conversation.updatedAt, style: .relative)
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
            .navigationTitle("Calculadora")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { showingNewConversation = true } label: {
                        Label("Conversa nova", systemImage: "square.and.pencil")
                    }
                }
            }
        } detail: {
            if let selectedID {
                ChatView(repository: repository, conversationID: selectedID)
                    .id(selectedID)
            } else {
                CalculatorWelcomeView { showingNewConversation = true }
            }
        }
        .task { model.reload() }
        .sheet(isPresented: $showingNewConversation, onDismiss: { model.reload() }) {
            NavigationStack {
                ChatView(repository: repository, conversationID: nil)
            }
        }
        .alert("Canvia el nom", isPresented: Binding(
            get: { renameTarget != nil },
            set: { if !$0 { renameTarget = nil } }
        )) {
            TextField("Títol", text: $renameText)
            Button("Desa") {
                if let target = renameTarget { model.rename(target.id, title: renameText) }
                renameTarget = nil
            }
            Button("Cancel·la", role: .cancel) { renameTarget = nil }
        }
    }
}

@MainActor
@Observable
public final class ChatViewModel {
    public var draft = ""
    public private(set) var conversation: ChatConversation?
    public private(set) var isSending = false
    public var errorMessage: String?
    private var conversationID: UUID?
    private let repository: any ChatRepository

    public init(repository: any ChatRepository, conversationID: UUID?) {
        self.repository = repository
        self.conversationID = conversationID
    }

    public func load() {
        guard let conversationID else { return }
        do {
            conversation = try repository.loadConversation(id: conversationID)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func send() async {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        draft = ""
        isSending = true
        errorMessage = nil
        do {
            let id: UUID
            if let conversationID {
                id = conversationID
            } else {
                id = try repository.createConversation(title: text)
                conversationID = id
            }
            conversation = try await repository.send(message: text, in: id)
        } catch {
            errorMessage = error.localizedDescription
            load()
        }
        isSending = false
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

public struct ChatView: View {
    @State private var model: ChatViewModel
    @Environment(\.dismiss) private var dismiss

    public init(repository: any ChatRepository, conversationID: UUID?) {
        _model = State(initialValue: ChatViewModel(repository: repository, conversationID: conversationID))
    }

    public var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        if model.conversation?.messages.isEmpty ?? true {
                            PromptSuggestions { suggestion in
                                model.draft = suggestion
                                Task { await model.send() }
                            }
                        }
                        ForEach(model.conversation?.messages ?? []) { message in
                            MessageBubble(message: message) {
                                Task { await model.retry(message.id) }
                            }
                            .id(message.id)
                        }
                        if model.isSending {
                            HStack { ProgressView(); Text("Calculant…").foregroundStyle(.secondary); Spacer() }
                                .padding(.horizontal)
                        }
                    }
                    .padding()
                }
                .onChange(of: model.conversation?.messages.count ?? 0) { _, _ in
                    if let last = model.conversation?.messages.last?.id {
                        withAnimation { proxy.scrollTo(last, anchor: .bottom) }
                    }
                }
            }

            if let error = model.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
            }

            HStack(alignment: .bottom, spacing: 10) {
                TextField("Pregunta o escriu dues actuacions…", text: $model.draft, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...5)
                    .onSubmit { Task { await model.send() } }
                Button { Task { await model.send() } } label: {
                    Image(systemName: "arrow.up.circle.fill").font(.title2)
                }
                .disabled(model.draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || model.isSending)
                .accessibilityLabel("Envia")
            }
            .padding()
            .background(.bar)
        }
        .navigationTitle(model.conversation?.title ?? "Conversa nova")
        .calculatorInlineNavigationTitle()
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                if model.conversation == nil {
                    Button("Tanca") { dismiss() }
                }
            }
        }
        .task { model.load() }
    }
}

private extension View {
    @ViewBuilder
    func calculatorInlineNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }
}

private struct MessageBubble: View {
    let message: ChatMessage
    let retry: () -> Void

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 44) }
            VStack(alignment: .leading, spacing: 8) {
                Text(message.content).textSelection(.enabled)
                if let calculation = message.calculation, !calculation.performances.isEmpty {
                    Divider()
                    ForEach(calculation.performances, id: \.label) { performance in
                        HStack {
                            Text(performance.label).fontWeight(.semibold)
                            Spacer()
                            Text(performance.total.formatted(.number.grouping(.automatic)))
                                .monospacedDigit()
                        }
                        .font(.caption)
                    }
                }
                if message.deliveryState == .failed {
                    Button("Torna-ho a provar", action: retry).font(.caption)
                }
            }
            .padding(11)
            .background(message.role == .user ? Color.accentColor : Color.secondary.opacity(0.12))
            .foregroundStyle(message.role == .user ? Color.white : Color.primary)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            if message.role == .assistant { Spacer(minLength: 44) }
        }
    }
}

private struct PromptSuggestions: View {
    let select: (String) -> Void
    private let prompts = [
        "Què guanya, el 5d9f o el 4d9fa?",
        "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?",
        "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Prova una comparació").font(.headline)
            ForEach(prompts, id: \.self) { prompt in
                Button(prompt) { select(prompt) }
                    .buttonStyle(.bordered)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct CalculatorWelcomeView: View {
    let create: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("Calculadora castellera", systemImage: "function")
        } description: {
            Text("Compara castells o actuacions amb la taula oficial del Concurs 2026.")
        } actions: {
            Button("Conversa nova", action: create).buttonStyle(.borderedProminent)
        }
    }
}
