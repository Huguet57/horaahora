import SwiftUI

struct AgendaEventListContent: View {
    let model: AgendaViewModel

    @ViewBuilder
    var body: some View {
        if model.isLoading && model.events.isEmpty {
            ProgressView()
                .frame(maxWidth: .infinity)
        } else if !model.events.isEmpty {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(model.events) { event in
                    AgendaEventCard(event: event)
                }
            }
        } else if model.errorMessage != nil {
            OfficialAgendaFallback(
                officialURL: model.officialURL,
                message: "No s'ha pogut connectar al servidor."
            ) {
                Task { await model.refresh() }
            }
        } else if model.sourceStatus == .unavailable {
            OfficialAgendaFallback(
                officialURL: model.officialURL,
                message: "Les dades natives no estan disponibles ara mateix."
            ) {
                Task { await model.refresh() }
            }
        } else {
            Text("No hi ha actuacions aquest dia")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
        }
    }
}

private struct OfficialAgendaFallback: View {
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
