import Foundation
import SwiftUI
import CastellsDomain

struct ConversationRow: View {
    let conversation: ChatConversationSummary
    let referenceDate: Date

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(conversation.title)
                .lineLimit(1)
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
}
