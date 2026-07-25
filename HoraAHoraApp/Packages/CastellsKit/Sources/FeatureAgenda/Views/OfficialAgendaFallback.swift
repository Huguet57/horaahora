import SwiftUI

struct OfficialAgendaFallback: View {
    let officialURL: URL
    let message: String
    let retry: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "wifi.exclamationmark")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 24, height: 24)

            VStack(alignment: .leading, spacing: 8) {
                Text("Agenda temporalment no disponible")
                    .font(.subheadline.weight(.semibold))

                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: 16) {
                    Button(action: retry) {
                        Label("Torna-ho a provar", systemImage: "arrow.clockwise")
                    }

                    Link(destination: officialURL) {
                        Label("Agenda oficial", systemImage: "arrow.up.right")
                    }
                }
                .font(.caption.weight(.medium))
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 12))
    }
}
