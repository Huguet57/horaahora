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
                Text("No hi ha actuacions de les colles seleccionades")
                    .font(.subheadline.weight(.medium))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 4)
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

    private var disclosureButton: some View {
        Button {
            toggleDisclosure()
        } label: {
            HStack(spacing: 10) {
                Image(systemName: "list.bullet")
                    .font(.caption.weight(.semibold))

                Text("Altres actuacions del dia · \(events.count)")
                    .font(.subheadline.weight(.semibold))

                Spacer(minLength: 8)

                Image(systemName: disclosure.isExpanded ? "chevron.up" : "chevron.down")
                    .font(.caption.weight(.semibold))
            }
            .foregroundStyle(.secondary)
            .padding(.horizontal, 14)
            .frame(minHeight: 44, alignment: .leading)
            .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 12))
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

    private func toggleDisclosure() {
        withAnimation(reduceMotion ? nil : .snappy(duration: 0.2)) {
            disclosure.toggle()
        }
    }
}
