import Foundation
import SwiftUI
import CastellsDomain

struct ConversationSidebar: View {
    let conversations: [ChatConversationSummary]
    @Binding var selection: CalculatorDestination?
    let onCreate: () -> Void
    let onDelete: (UUID) -> Void
    let onRename: (ChatConversationSummary) -> Void

    var body: some View {
        TimelineView(.periodic(from: .now, by: 60)) { context in
            List(selection: $selection) {
                if conversations.isEmpty {
                    ContentUnavailableView {
                        Label("Cap conversa", systemImage: "bubble.left.and.bubble.right")
                    } description: {
                        Text("Crea una conversa per comparar castells i actuacions.")
                    }
                    .listRowBackground(Color.clear)
                }

                ForEach(conversations) { conversation in
                    let destination = CalculatorDestination.conversation(conversation.id)
                    Button { selection = destination } label: {
                        HStack {
                            ConversationRow(
                                conversation: conversation,
                                referenceDate: context.date
                            )
                            Spacer(minLength: 8)
                            Image(systemName: "chevron.forward")
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(.tertiary)
                        }
                    }
                    .tag(destination)
                    .selectionDisabled()
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) { onDelete(conversation.id) } label: {
                            Label("Elimina", systemImage: "trash")
                        }
                        Button { onRename(conversation) } label: {
                            Label("Canvia el nom", systemImage: "pencil")
                        }
                        .tint(.gray)
                    }
                }
            }
        }
        .navigationTitle("Calculadora")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: onCreate) {
                    Label("Conversa nova", systemImage: "square.and.pencil")
                }
            }
        }
    }
}
