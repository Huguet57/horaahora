import SwiftUI

struct AgendaGroupFilterRow: View {
    let groupName: String
    let isFollowing: Bool
    let isFeatured: Bool
    let onToggleFollowing: () -> Void
    let onToggleFeatured: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button(action: onToggleFollowing) {
                HStack(spacing: 12) {
                    Image(systemName: isFollowing ? "checkmark.square.fill" : "square")
                        .foregroundStyle(isFollowing ? Color.accentColor : Color.secondary)
                    Text(groupName)
                        .foregroundStyle(.primary)
                        .multilineTextAlignment(.leading)
                    Spacer(minLength: 0)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(groupName)
            .accessibilityValue(isFollowing ? "Seleccionada" : "No seleccionada")
            .accessibilityAddTraits(isFollowing ? .isSelected : [])

            Button(action: onToggleFeatured) {
                Image(systemName: isFeatured ? "star.fill" : "star")
                    .foregroundStyle(isFeatured ? Color.yellow : Color.secondary)
                    .frame(width: 36, height: 36)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(
                isFeatured
                    ? "Treu \(groupName) de colles destacades"
                    : "Destaca \(groupName)"
            )
        }
    }
}
