#if os(iOS)
import SwiftUI

/// The result of a cell's castell as a grid of four, opened from its D/C badge. Tapping one sets
/// it and closes the modal.
struct ComparatorOutcomeSheet: View {
    let store: ComparatorStore
    let cell: ComparatorCell

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        if let colla = store.colla(cell.collaID), let castell = colla.rounds[cell.round] {
            VStack(spacing: 14) {
                Text("\(colla.name) · Ronda \(cell.round + 1) · \(castell.notation)")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                ComparatorOutcomeGrid(current: castell.outcome) { outcome in
                    store.setOutcome(outcome, at: cell)
                    dismiss()
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 22)
            .frame(maxHeight: .infinity, alignment: .top)
        }
    }
}

/// Descarregat, carregat, intent and intent desmuntat as four big buttons, the current one
/// filled.
struct ComparatorOutcomeGrid: View {
    let current: ComparatorOutcome?
    let onPick: (ComparatorOutcome) -> Void

    var body: some View {
        Grid(horizontalSpacing: 10, verticalSpacing: 10) {
            GridRow {
                option(.unloaded)
                option(.loaded)
            }
            GridRow {
                option(.attempt)
                option(.dismantledAttempt)
            }
        }
    }

    private func option(_ outcome: ComparatorOutcome) -> some View {
        let isCurrent = current == outcome
        return Button {
            onPick(outcome)
        } label: {
            VStack(spacing: 4) {
                Text(outcome.shortLabel)
                    .font(.title.weight(.heavy))
                Text(outcome.label)
                    .font(.caption.weight(.medium))
            }
            .foregroundStyle(isCurrent ? Color.white : outcome.color)
            .frame(maxWidth: .infinity, minHeight: 80)
            .background(
                isCurrent ? AnyShapeStyle(outcome.color) : AnyShapeStyle(outcome.color.opacity(0.14)),
                in: .rect(cornerRadius: 14)
            )
            .contentShape(.rect(cornerRadius: 14))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isCurrent ? .isSelected : [])
    }
}
#endif
