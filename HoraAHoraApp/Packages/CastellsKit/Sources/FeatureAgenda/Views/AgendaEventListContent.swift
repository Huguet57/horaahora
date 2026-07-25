import SwiftUI
import CastellsDomain

/// The event cards do not depend on fold progress. Equality by snapshot keeps
/// this subtree out of the scroll hot path while agenda changes still render.
struct AgendaEventListContent: View, Equatable {
    let events: [CastellEvent]
    let isLoading: Bool
    let errorMessage: String?
    let sourceStatus: AgendaSourceStatus
    let officialURL: URL
    let refresh: () -> Void

    nonisolated static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.events == rhs.events
            && lhs.isLoading == rhs.isLoading
            && lhs.errorMessage == rhs.errorMessage
            && lhs.sourceStatus == rhs.sourceStatus
            && lhs.officialURL == rhs.officialURL
    }

    @ViewBuilder
    var body: some View {
        if isLoading && events.isEmpty {
            ProgressView()
                .frame(maxWidth: .infinity)
        } else if !events.isEmpty {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(events) { event in
                    AgendaEventCard(event: event)
                }
            }
        } else if errorMessage != nil {
            OfficialAgendaFallback(
                officialURL: officialURL,
                message: "No s'ha pogut connectar al servidor."
            ) { refresh() }
        } else if sourceStatus == .unavailable {
            OfficialAgendaFallback(
                officialURL: officialURL,
                message: "Les dades natives no estan disponibles ara mateix."
            ) { refresh() }
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
