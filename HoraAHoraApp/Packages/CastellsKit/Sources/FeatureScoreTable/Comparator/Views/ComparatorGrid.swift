#if os(iOS)
import SwiftUI

/// The five rounds down and the colles across. Tapping a cell opens the castell modal for it;
/// tapping its D/C badge, the result picker; swiping the selected one up or down steps it.
struct ComparatorGrid: View {
    let store: ComparatorStore
    let ranking: [ComparatorStanding]
    let columnWidth: CGFloat
    let onTap: (ComparatorCell) -> Void
    let onTapOutcome: (ComparatorCell) -> Void

    private var colles: [ComparatorColla] { store.current.colles }

    var body: some View {
        VStack(spacing: 6) {
            ForEach(0..<ComparatorColla.roundCount, id: \.self) { round in
                HStack(spacing: 6) {
                    Text("R\(round + 1)")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                        .frame(width: comparatorGutterWidth)
                    ForEach(colles) { colla in
                        cell(colla, round: round)
                    }
                    if colles.count < ComparatorStore.maxColles {
                        Color.clear.frame(width: comparatorAddColumnWidth)
                    }
                }
            }
        }
    }

    private func cell(_ colla: ComparatorColla, round: Int) -> some View {
        let cell = ComparatorCell(collaID: colla.id, round: round)
        let castell = colla.rounds[round]
        let roundScore = ranking.first { $0.collaID == colla.id }?.score.rounds[round]
        let restriction = castell.flatMap { store.rules.restriction(of: $0.notation, inRound: round, for: colla) }
        let isSelected = store.selection == cell
        return ComparatorCellView(
            castell: castell,
            roundScore: roundScore,
            restriction: restriction,
            isSelected: isSelected,
            isCompact: colles.count > 2,
            onTapOutcome: { onTapOutcome(cell) }
        )
        .frame(width: columnWidth)
        .id(cell.id)
        .contentShape(.rect(cornerRadius: 12))
        .onTapGesture { onTap(cell) }
        .gesture(isSelected ? stepSwipe(cell) : nil)
        .contextMenu {
            if castell != nil {
                ForEach(ComparatorOutcome.allCases, id: \.self) { outcome in
                    Button(outcome.label) { store.setOutcome(outcome, at: cell) }
                }
                Divider()
                Button("Buida la ronda", systemImage: "trash", role: .destructive) {
                    store.set(nil, at: cell)
                    if store.selection == cell { store.selection = nil }
                }
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(colla.name), ronda \(round + 1)")
        .accessibilityValue(castell.map { "\($0.notation), \($0.outcome.label)" } ?? "buida")
        .accessibilityAddTraits(.isButton)
        .accessibilityAdjustableAction { direction in
            store.step(cell, by: direction == .increment ? 1 : -1)
        }
    }

    private func stepSwipe(_ cell: ComparatorCell) -> some Gesture {
        DragGesture(minimumDistance: 14)
            .onEnded { value in
                let dy = value.translation.height
                guard abs(dy) > abs(value.translation.width), abs(dy) > 20 else { return }
                store.step(cell, by: dy < 0 ? 1 : -1)
            }
    }
}

struct ComparatorCellView: View {
    let castell: PlannedCastell?
    let roundScore: RoundScore?
    let restriction: ComparatorRestriction?
    let isSelected: Bool
    let isCompact: Bool
    var onTapOutcome: () -> Void = {}

    var body: some View {
        Group {
            if let castell {
                filled(castell)
            } else {
                empty
            }
        }
        .frame(maxWidth: .infinity, minHeight: isCompact ? 54 : 62)
        .background(background, in: .rect(cornerRadius: 12))
        .overlay {
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(isSelected ? Color.accentColor : .clear, lineWidth: 2)
        }
    }

    private var background: Color {
        castell == nil ? Color(.secondarySystemGroupedBackground).opacity(0.5) : Color(.secondarySystemGroupedBackground)
    }

    private var empty: some View {
        RoundedRectangle(cornerRadius: 12)
            .strokeBorder(style: StrokeStyle(lineWidth: 1, dash: [4, 3]))
            .foregroundStyle(Color(.tertiaryLabel))
            .overlay {
                Label(isCompact ? "" : "castell", systemImage: "plus")
                    .labelStyle(.titleAndIcon)
                    .font(.footnote.weight(.medium))
                    .foregroundStyle(.secondary)
            }
    }

    private var notCountedReason: NotCountedReason? {
        if case let .notCounted(reason) = roundScore?.status { reason } else { nil }
    }

    private func filled(_ castell: PlannedCastell) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(spacing: 4) {
                Text(castell.notation)
                    .font((isCompact ? Font.footnote : .callout).monospaced().weight(.semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.6)
                Spacer(minLength: 0)
                Button(action: onTapOutcome) {
                    ComparatorOutcomeBadge(outcome: castell.outcome, isCompact: isCompact)
                }
                .buttonStyle(.plain)
                // A bigger target than the badge itself, which is small to tap.
                .contentShape(.rect.inset(by: -10))
                .accessibilityLabel("Resultat: \(castell.outcome.label)")
            }
            HStack(spacing: 4) {
                if let restriction {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    if !isCompact {
                        Text(restriction.label).foregroundStyle(.orange)
                    }
                } else if let notCountedReason {
                    Text(isCompact ? "no compta" : "no compta · \(notCountedReason.label)")
                        .foregroundStyle(.secondary)
                } else {
                    Text(formattedPoints(roundScore?.points ?? 0))
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                }
            }
            .font(.caption2)
            .lineLimit(1)
            .minimumScaleFactor(0.7)
        }
        .padding(.horizontal, isCompact ? 7 : 10)
        .padding(.vertical, 8)
        .opacity(notCountedReason == nil ? 1 : 0.5)
    }
}

struct ComparatorOutcomeBadge: View {
    let outcome: ComparatorOutcome
    var isCompact = false

    var body: some View {
        Text(outcome.shortLabel)
            .font((isCompact ? Font.caption2 : .caption).weight(.heavy))
            .foregroundStyle(.white)
            .padding(.horizontal, isCompact ? 4 : 6)
            .frame(minWidth: isCompact ? 16 : 22, minHeight: isCompact ? 16 : 20)
            .background(outcome.color, in: .rect(cornerRadius: 5))
    }
}

extension ComparatorOutcome {
    var color: Color {
        switch self {
        case .unloaded: Color(.systemGreen)
        case .loaded: Color.accentColor
        case .attempt, .dismantledAttempt: Color(.systemGray)
        }
    }
}
#endif
