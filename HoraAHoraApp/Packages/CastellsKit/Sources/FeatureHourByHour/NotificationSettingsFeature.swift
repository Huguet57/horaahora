import SwiftUI
#if os(iOS)
import UIKit
#endif

struct HourByHourNotificationOnboardingCard: View {
    let onConfigure: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "bell.badge.fill")
                .font(.title2)
                .foregroundStyle(.tint)
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 5) {
                Text("Vols rebre les novetats?")
                    .font(.headline)
                Text("Activa els avisos de l'Hora a Hora quan tu vulguis.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button("Configura-ho") { onConfigure() }
                    .font(.subheadline.weight(.semibold))
                    .padding(.top, 2)
            }

            Spacer(minLength: 0)

            Button(action: onDismiss) {
                Image(systemName: "xmark")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)
                    .padding(6)
            }
            .accessibilityLabel("Ara no")
        }
        .padding(14)
        .background(cardBackground, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private var cardBackground: Color {
        #if os(iOS)
        Color(uiColor: .secondarySystemFill)
        #else
        Color.secondary.opacity(0.2)
        #endif
    }
}
