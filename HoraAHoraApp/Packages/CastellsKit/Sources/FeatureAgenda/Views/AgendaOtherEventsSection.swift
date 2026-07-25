import SwiftUI
import CastellsDomain

struct AgendaOtherEventsSection: View {
    let events: [CastellEvent]
    let hasMatchingEvents: Bool
    @State private var disclosure: AgendaOtherEventsDisclosureState
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    init(
        events: [CastellEvent],
        hasMatchingEvents: Bool
    ) {
        self.events = events
        self.hasMatchingEvents = hasMatchingEvents
        _disclosure = State(
            initialValue: AgendaOtherEventsDisclosureState(
                hasMatchingEvents: hasMatchingEvents
            )
        )
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if !hasMatchingEvents {
                noMatchesMessage
            }

            disclosureButton

            if disclosure.isExpanded {
                ForEach(events) { event in
                    AgendaEventCard(event: event, isOutsideFilter: true)
                        .id("other:\(event.id)")
                }
            }
        }
    }

    private var noMatchesMessage: some View {
        Text("Cap actuació coincideix amb les colles seleccionades")
            .font(.subheadline.weight(.medium))
            .multilineTextAlignment(.center)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
    }

    private var disclosureButton: some View {
        Button {
            withAnimation(reduceMotion ? nil : .snappy(duration: 0.2)) {
                disclosure.toggle()
            }
        } label: {
            HStack(spacing: 10) {
                Label(
                    "Altres actuacions del dia · \(events.count)",
                    systemImage: "line.3.horizontal.decrease"
                )
                Spacer(minLength: 8)
                Image(systemName: disclosure.isExpanded ? "chevron.up" : "chevron.down")
                    .font(.caption.weight(.semibold))
            }
            .font(.subheadline.weight(.semibold))
            .foregroundStyle(.secondary)
            .padding(.horizontal, 14)
            .frame(minHeight: 44)
            .background(Color.secondary.opacity(0.09), in: RoundedRectangle(cornerRadius: 12))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Altres actuacions del dia")
        .accessibilityValue(
            "\(events.count), \(disclosure.isExpanded ? "desplegades" : "plegades")"
        )
        .accessibilityHint(
            disclosure.isExpanded ? "Plega les actuacions" : "Mostra les actuacions"
        )
    }
}
