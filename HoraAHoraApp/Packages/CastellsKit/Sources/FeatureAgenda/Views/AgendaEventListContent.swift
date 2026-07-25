import SwiftUI
import CastellsDomain

/// The event cards do not depend on fold progress. Equality by snapshot keeps
/// this subtree out of the scroll hot path while agenda changes still render.
struct AgendaEventListContent: View, Equatable {
    let events: [CastellEvent]
    let otherEvents: [CastellEvent]
    let isLoading: Bool
    let errorMessage: String?
    let sourceStatus: AgendaSourceStatus
    let officialURL: URL
    let refresh: () -> Void

    nonisolated static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.events == rhs.events
            && lhs.otherEvents == rhs.otherEvents
            && lhs.isLoading == rhs.isLoading
            && lhs.errorMessage == rhs.errorMessage
            && lhs.sourceStatus == rhs.sourceStatus
            && lhs.officialURL == rhs.officialURL
    }

    @ViewBuilder
    var body: some View {
        if isLoading && events.isEmpty && otherEvents.isEmpty {
            ProgressView()
                .frame(maxWidth: .infinity)
        } else if !events.isEmpty || !otherEvents.isEmpty {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(events) { event in
                    AgendaEventCard(event: event)
                        .id("selected:\(event.id)")
                }

                if !otherEvents.isEmpty {
                    VStack(spacing: 6) {
                        HStack(spacing: 12) {
                            Divider()
                            Label("Altres actuacions", systemImage: "line.3.horizontal.decrease")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.secondary)
                                .fixedSize()
                            Divider()
                        }

                        if events.isEmpty {
                            Text("Cap actuació coincideix amb les colles seleccionades")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 4)

                    ForEach(otherEvents) { event in
                        AgendaEventCard(event: event, isOutsideFilter: true)
                            .id("other:\(event.id)")
                    }
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
