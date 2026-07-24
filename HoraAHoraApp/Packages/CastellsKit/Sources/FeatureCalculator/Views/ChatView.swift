import SwiftUI
import CastellsDomain

public struct ChatView: View {
    @State private var model: ChatViewModel
    @FocusState private var isComposerFocused: Bool

    public init(
        repository: any ChatRepository,
        conversationID: UUID?,
        onConversationCreated: @escaping @MainActor () -> Void = {}
    ) {
        _model = State(initialValue: ChatViewModel(
            repository: repository,
            conversationID: conversationID,
            onConversationCreated: onConversationCreated
        ))
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
                        withAnimation {
                            proxy.scrollTo("assistant-response-skeleton", anchor: .bottom)
                        }
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
                TextField(
                    "Pregunta o escriu dues actuacions…",
                    text: $model.draft,
                    axis: .vertical
                )
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...5)
                .focused($isComposerFocused)
                .onSubmit { Task { await model.send() } }
                Button { Task { await model.send() } } label: {
                    Image(systemName: "arrow.up.circle.fill").font(.title2)
                }
                .disabled(
                    model.draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        || model.isSending
                )
                .accessibilityLabel("Envia")
            }
            .padding()
            .background(.bar)
        }
        .navigationTitle(model.conversation?.title ?? "Conversa nova")
        .calculatorInlineNavigationTitle()
        .task { await model.loadFollowingPendingResponse() }
    }
}

struct AssistantResponseSkeleton: View {
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

extension View {
    @ViewBuilder
    func calculatorInlineNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }

    @ViewBuilder
    func calculatorTabBarVisibility(isChatPresented: Bool) -> some View {
        #if os(iOS)
        toolbar(isChatPresented ? .hidden : .automatic, for: .tabBar)
        #else
        self
        #endif
    }
}
