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
                ChatView(repository: repository, conversationID: nil)
                    .id(selectedDestination)
                    .onDisappear { model.reload() }
            case nil:
                CalculatorWelcomeView { showNewConversation() }
            }
        }
        .task { model.reload() }
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

    private func showNewConversation() {
        selectedDestination = .newConversation
        preferredCompactColumn = .detail
    }
}

private enum CalculatorDestination: Hashable {
    case conversation(UUID)
    case newConversation
}

@MainActor
@Observable
public final class ChatViewModel {
    typealias Sleep = @MainActor @Sendable (Duration) async throws -> Void

    public var draft = ""
    public private(set) var conversation: ChatConversation?
    public private(set) var pendingUserMessage: ChatMessage?
    public private(set) var isSending = false
    public var errorMessage: String?
    private var conversationID: UUID?
    private let repository: any ChatRepository
    private let sleep: Sleep

    public convenience init(repository: any ChatRepository, conversationID: UUID?) {
        self.init(
            repository: repository,
            conversationID: conversationID,
            sleep: { duration in try await ContinuousClock().sleep(for: duration) }
        )
    }

    init(
        repository: any ChatRepository,
        conversationID: UUID?,
        sleep: @escaping Sleep
    ) {
        self.repository = repository
        self.conversationID = conversationID
        self.sleep = sleep
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
    @FocusState private var isComposerFocused: Bool

    public init(repository: any ChatRepository, conversationID: UUID?) {
        _model = State(initialValue: ChatViewModel(repository: repository, conversationID: conversationID))
    }

    public var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                GeometryReader { geometry in
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            if model.showsPromptSuggestions {
                                PromptSuggestions { suggestion in
                                    model.draft = suggestion
                                    Task { await model.send() }
                                }
                            }
                            ForEach(model.displayedMessages) { message in
                                MessageBubble(message: message) {
                                    Task { await model.retry(message.id) }
                                }
                                .id(message.id)
                            }
                            if model.isSending {
                                AssistantResponseSkeleton()
                                    .id("assistant-response-skeleton")
                            }
                        }
                        .padding()
                        .frame(
                            maxWidth: .infinity,
                            minHeight: geometry.size.height,
                            alignment: .top
                        )
                        .contentShape(Rectangle())
                        .simultaneousGesture(TapGesture().onEnded {
                            isComposerFocused = false
                        })
                    }
                    .scrollDismissesKeyboard(.interactively)
                    .scrollBounceBehavior(.always, axes: .vertical)
                }
                .onChange(of: model.displayedMessages.count) { _, _ in
                    if let last = model.displayedMessages.last?.id {
                        withAnimation { proxy.scrollTo(last, anchor: .bottom) }
                    }
                }
                .onChange(of: model.isSending) { _, isSending in
                    if isSending {
                        withAnimation { proxy.scrollTo("assistant-response-skeleton", anchor: .bottom) }
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
                    .focused($isComposerFocused)
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
        .calculatorChatHidesTabBar()
        .task { await model.loadFollowingPendingResponse() }
    }
}

private struct AssistantResponseSkeleton: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isPulsing = false

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 10) {
                skeletonLine(width: 205, height: 17)
                Divider()

                HStack(spacing: 7) {
                    skeletonLine(width: 18, height: 18)
                    skeletonLine(width: 88, height: 13)
                }

                VStack(spacing: 9) {
                    HStack {
                        skeletonLine(width: 56, height: 12)
                        Spacer()
                        skeletonLine(width: 82, height: 12)
                        skeletonLine(width: 82, height: 12)
                    }
                    Divider()
                    HStack {
                        skeletonLine(width: 14, height: 12)
                        Spacer()
                        skeletonLine(width: 76, height: 30)
                        skeletonLine(width: 76, height: 30)
                    }
                    Divider()
                    HStack {
                        skeletonLine(width: 42, height: 13)
                        Spacer()
                        skeletonLine(width: 64, height: 13)
                        skeletonLine(width: 64, height: 13)
                    }
                }
                .padding(10)
                .background(Color.primary.opacity(0.04))
                .clipShape(RoundedRectangle(cornerRadius: 11))

                skeletonLine(width: 150, height: 13)
            }
            .padding(11)
            .frame(maxWidth: 360, alignment: .leading)
            .background(Color.secondary.opacity(0.12))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .opacity(reduceMotion ? 0.68 : (isPulsing ? 0.44 : 0.78))

            Spacer(minLength: 44)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Preparant la resposta")
        .onAppear {
            guard !reduceMotion else { return }
            withAnimation(.easeInOut(duration: 0.85).repeatForever(autoreverses: true)) {
                isPulsing = true
            }
        }
    }

    private func skeletonLine(width: CGFloat, height: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: min(height / 2, 6))
            .fill(Color.secondary.opacity(0.38))
            .frame(width: width, height: height)
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

    @ViewBuilder
    func calculatorChatHidesTabBar() -> some View {
        #if os(iOS)
        toolbar(.hidden, for: .tabBar)
        #else
        self
        #endif
    }
}

struct ComparisonPresentation {
    struct Castell: Identifiable {
        let id: Int
        let notation: String
        let result: String
        let points: Int
        let counted: Bool
    }

    struct Column: Identifiable {
        let id: Int
        let label: String
        let total: Int
        let castells: [Castell]
        let isWinner: Bool
    }

    let columns: [Column]
    let winnerLabel: String?
    let margin: Int?
    let summary: String
    let maximumCastellCount: Int

    init?(response: ChatResponse) {
        guard
            response.intent == "comparison",
            response.performances.count >= 2,
            !response.needsClarification
        else {
            return nil
        }

        let displayLabels = Self.displayLabels(for: response.performances)
        columns = response.performances.enumerated().map { columnIndex, performance in
            Column(
                id: columnIndex,
                label: displayLabels[columnIndex],
                total: performance.total,
                castells: performance.castells.enumerated().map { castellIndex, castell in
                    Castell(
                        id: castellIndex,
                        notation: castell.canonical ?? castell.input,
                        result: Self.resultLabel(castell.outcome),
                        points: castell.points,
                        counted: castell.counted
                    )
                },
                isWinner: performance.label == response.winnerLabel
            )
        }
        maximumCastellCount = columns.map(\.castells.count).max() ?? 0

        if let sourceWinner = response.winnerLabel,
           let winnerIndex = response.performances.firstIndex(where: { $0.label == sourceWinner }) {
            winnerLabel = displayLabels[winnerIndex]
        } else {
            winnerLabel = nil
        }

        if let winner = winnerLabel {
            let totals = response.performances.map(\.total).sorted(by: >)
            let winningMargin = totals[0] - totals[1]
            margin = winningMargin
            summary = "Guanya \(winner) per \(winningMargin.formatted(.number.grouping(.automatic))) punts."
        } else {
            margin = nil
            let total = response.performances.first?.total ?? 0
            summary = "Empat a \(total.formatted(.number.grouping(.automatic))) punts."
        }
    }

    private static func displayLabels(for performances: [PerformanceResponse]) -> [String] {
        guard performances.count >= 2 else { return performances.map(\.label) }

        let notationSets = performances.map { performance in
            Set(performance.castells.map { compact($0.input) })
        }
        let generic = performances.map { isGenericLabel($0.label, performance: $0) }
        var used = Set(
            performances.enumerated().compactMap { index, performance in
                generic[index] ? nil : compact(performance.label)
            }
        )
        var labels: [String?] = []

        for (index, performance) in performances.enumerated() {
            guard generic[index] else {
                labels.append(performance.label.trimmingCharacters(in: .whitespacesAndNewlines))
                continue
            }

            let otherNotations = notationSets.enumerated().reduce(into: Set<String>()) { result, item in
                if item.offset != index { result.formUnion(item.element) }
            }
            let distinctive = performance.castells.first {
                !otherNotations.contains(compact($0.input))
            }?.input.trimmingCharacters(in: .whitespacesAndNewlines)
            let proposed = distinctive.map { "Amb \($0)" }
            if let proposed, !used.contains(compact(proposed)) {
                labels.append(proposed)
                used.insert(compact(proposed))
            } else {
                labels.append(nil)
            }
        }

        let alphabet = Array("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for index in labels.indices where labels[index] == nil {
            var candidateIndex = index
            var fallback: String
            repeat {
                fallback = candidateIndex < alphabet.count
                    ? String(alphabet[candidateIndex])
                    : "A\(candidateIndex + 1)"
                candidateIndex += 1
            } while used.contains(compact(fallback))
            labels[index] = fallback
            used.insert(compact(fallback))
        }

        return labels.compactMap { $0 }
    }

    private static func isGenericLabel(
        _ label: String,
        performance: PerformanceResponse
    ) -> Bool {
        let normalized = compact(label)
        if normalized.count == 1, normalized.first?.isLetter == true { return true }

        let parts = normalized.split(separator: " ").map(String.init)
        let genericRoots = ["costat", "opció", "opcio", "actuació", "actuacio"]
        if parts.count == 2,
           genericRoots.contains(parts[0]),
           (Int(parts[1]) != nil || (parts[1].count == 1 && parts[1].first?.isLetter == true)) {
            return true
        }

        let compactWithoutSpaces = normalized.replacingOccurrences(of: " ", with: "")
        return performance.castells.contains { castell in
            compact(castell.input).replacingOccurrences(of: " ", with: "") == compactWithoutSpaces
                || compact(castell.canonical ?? "").replacingOccurrences(of: " ", with: "") == compactWithoutSpaces
        }
    }

    private static func compact(_ value: String) -> String {
        value
            .lowercased()
            .split(whereSeparator: \.isWhitespace)
            .joined(separator: " ")
    }

    private static func resultLabel(_ outcome: String) -> String {
        switch outcome {
        case "loaded": "Carregat"
        case "unloaded": "Descarregat"
        case "attempt": "Intent"
        default: outcome.capitalized
        }
    }
}

private struct MessageBubble: View {
    let message: ChatMessage
    let retry: () -> Void

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 44) }
            VStack(alignment: .leading, spacing: 8) {
                if let comparison {
                    Text(comparison.summary).textSelection(.enabled)
                    Divider()
                    ComparisonTable(presentation: comparison)
                } else {
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

    private var comparison: ComparisonPresentation? {
        message.calculation.flatMap(ComparisonPresentation.init(response:))
    }
}

private struct ComparisonTable: View {
    let presentation: ComparisonPresentation

    var body: some View {
        VStack(alignment: .leading, spacing: 9) {
            Label("Comparativa", systemImage: "tablecells")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)

            ScrollView(.horizontal, showsIndicators: false) {
                Grid(alignment: .leading, horizontalSpacing: 14, verticalSpacing: 8) {
                    GridRow {
                        Text("Castell")
                            .foregroundStyle(.secondary)
                        ForEach(presentation.columns) { column in
                            HStack(spacing: 4) {
                                if column.isWinner {
                                    Image(systemName: "trophy.fill")
                                        .foregroundStyle(.yellow)
                                }
                                Text(column.label)
                                    .fontWeight(.semibold)
                                    .lineLimit(1)
                            }
                            .frame(minWidth: 112, alignment: .trailing)
                        }
                    }
                    .font(.caption)

                    Divider()
                        .gridCellColumns(presentation.columns.count + 1)

                    ForEach(0..<presentation.maximumCastellCount, id: \.self) { index in
                        GridRow {
                            Text("\(index + 1)")
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                            ForEach(presentation.columns) { column in
                                castellCell(column, at: index)
                            }
                        }
                    }

                    Divider()
                        .gridCellColumns(presentation.columns.count + 1)

                    GridRow {
                        Text("Total")
                            .fontWeight(.semibold)
                        ForEach(presentation.columns) { column in
                            Text(column.total.formatted(.number.grouping(.automatic)))
                                .fontWeight(.bold)
                                .monospacedDigit()
                                .frame(minWidth: 112, alignment: .trailing)
                        }
                    }
                    .font(.caption)
                }
                .padding(10)
            }
            .background(Color.primary.opacity(0.045))
            .clipShape(RoundedRectangle(cornerRadius: 11))

            if let winner = presentation.winnerLabel, let margin = presentation.margin {
                Label(
                    "\(winner), +\(margin.formatted(.number.grouping(.automatic))) punts",
                    systemImage: "trophy.fill"
                )
                .font(.caption.weight(.semibold))
                .foregroundStyle(.primary)
            } else {
                Label("Empat", systemImage: "equal.circle.fill")
                    .font(.caption.weight(.semibold))
            }
        }
    }

    @ViewBuilder
    private func castellCell(_ column: ComparisonPresentation.Column, at index: Int) -> some View {
        if column.castells.indices.contains(index) {
            let castell = column.castells[index]
            VStack(alignment: .trailing, spacing: 2) {
                Text(castell.notation)
                    .font(.caption.monospaced().weight(.semibold))
                Text(detail(for: castell))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .frame(minWidth: 112, alignment: .trailing)
            .opacity(castell.counted ? 1 : 0.55)
        } else {
            Text("—")
                .foregroundStyle(.tertiary)
                .frame(minWidth: 112, alignment: .trailing)
        }
    }

    private func detail(for castell: ComparisonPresentation.Castell) -> String {
        let points = castell.points.formatted(.number.grouping(.automatic))
        let suffix = castell.counted ? "" : " · no compta"
        return "\(castell.result) · \(points)\(suffix)"
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
                Button {
                    select(prompt)
                } label: {
                    Text(prompt)
                        .multilineTextAlignment(.leading)
                }
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
            Label("Calculadora castellera", systemImage: "plus.forwardslash.minus")
        } description: {
            Text("Compara castells o actuacions amb la taula oficial del Concurs 2026.")
        } actions: {
            Button("Conversa nova", action: create).buttonStyle(.borderedProminent)
        }
    }
}
