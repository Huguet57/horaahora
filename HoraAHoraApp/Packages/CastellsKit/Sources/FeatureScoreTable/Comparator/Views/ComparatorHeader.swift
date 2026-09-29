#if os(iOS)
import SwiftUI

/// The width of the round labels on the left of the grid, which the header leaves free too.
let comparatorGutterWidth: CGFloat = 30
/// The slot after the last colla where the next one would go, empty in the grid.
let comparatorAddColumnWidth: CGFloat = 44

/// The widths the header and the grid share, so that their columns line up.
@MainActor
enum ComparatorLayout {
    static let horizontalPadding: CGFloat = 12
    static let spacing: CGFloat = 6
    /// Narrower columns cramp a castell and its result; past it the columns scroll sideways.
    static let minColumnWidth: CGFloat = 116

    /// The colla columns share what the screen leaves them, down to `minColumnWidth`.
    static func columnWidth(viewport: CGFloat, colles: Int) -> CGFloat {
        let hasAddSlot = colles < ComparatorStore.maxColles
        let gaps = CGFloat(colles + (hasAddSlot ? 1 : 0))
        let fixed = 2 * horizontalPadding + comparatorGutterWidth + spacing * gaps
            + (hasAddSlot ? comparatorAddColumnWidth : 0)
        return max(minColumnWidth, (viewport - fixed) / CGFloat(max(colles, 1)))
    }
}

/// The totals of each colla, its place and gap to the first, and who leads by how much.
struct ComparatorHeader: View {
    let store: ComparatorStore
    let ranking: [ComparatorStanding]
    let onEditColla: (UUID?) -> Void
    /// Every colla column is this wide, at least `ComparatorLayout.minColumnWidth`.
    let columnWidth: CGFloat
    /// The width on screen, which the summary keeps to while the columns scroll sideways.
    let viewportWidth: CGFloat

    private var colles: [ComparatorColla] { store.current.colles }
    private var isCompact: Bool { colles.count > 2 }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top, spacing: 6) {
                // Leaves the round labels' width free, so the columns line up with the grid's.
                Color.clear
                    .frame(width: comparatorGutterWidth, height: 1)
                ForEach(colles) { colla in
                    column(colla)
                }
                if colles.count < ComparatorStore.maxColles {
                    addButton
                }
            }
            .fixedSize(horizontal: false, vertical: true)
            summary
        }
        .padding(.vertical, 12)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 16))
    }

    private var addButton: some View {
        Button {
            onEditColla(nil)
        } label: {
            RoundedRectangle(cornerRadius: 10)
                .strokeBorder(style: StrokeStyle(lineWidth: 1, dash: [4, 3]))
                .foregroundStyle(Color(.tertiaryLabel))
                .overlay {
                    Image(systemName: "plus")
                        .font(.body.weight(.medium))
                        .foregroundStyle(.secondary)
                }
                .padding(.trailing, 8)
                .frame(width: comparatorAddColumnWidth)
                .frame(maxHeight: .infinity)
                .contentShape(.rect)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Afegeix una colla")
    }

    private func column(_ colla: ComparatorColla) -> some View {
        let position = (ranking.firstIndex { $0.collaID == colla.id } ?? 0) + 1
        let score = ranking.first { $0.collaID == colla.id }?.score
        let total = score?.total ?? 0
        let leaderTotal = ranking.first?.score.total ?? 0
        let isLeader = position == 1 && colles.count > 1 && total > 0
        return VStack(alignment: .leading, spacing: 2) {
            Menu {
                Button("Canvia la colla…", systemImage: "arrow.left.arrow.right") { onEditColla(colla.id) }
                Button("Afegeix una penalització", systemImage: "plus") {
                    store.changePenalties(of: colla.id, by: 1)
                }
                if colla.penalties > 0 {
                    Button("Treu una penalització", systemImage: "minus") {
                        store.changePenalties(of: colla.id, by: -1)
                    }
                }
                if colles.count > 1 {
                    Divider()
                    Button("Treu la colla", systemImage: "trash", role: .destructive) {
                        store.removeColla(colla.id)
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    if colles.count > 1 {
                        Text("\(position)")
                            .font(.caption2.weight(.bold))
                            .foregroundStyle(isLeader ? Color.white : Color.secondary)
                            .frame(width: 16, height: 16)
                            .background(isLeader ? Color.accentColor : Color(.tertiarySystemFill), in: .circle)
                    }
                    Text(isCompact ? colla.shortName : colla.name)
                        .font(.subheadline.weight(.semibold))
                        .lineLimit(1)
                        .minimumScaleFactor(0.7)
                        .foregroundStyle(.primary)
                }
            }
            .tint(.primary)
            Text(formattedPoints(total))
                .font(isCompact ? .title3.weight(.bold) : .title.weight(.bold))
                .fontDesign(.rounded)
                .monospacedDigit()
                .lineLimit(1)
                .minimumScaleFactor(0.6)
                .contentTransition(.numericText(value: Double(total)))
            // Always there, so that the header keeps its height as points come and go.
            if colles.count > 1 {
                Text(gap(position: position, total: total, leaderTotal: leaderTotal, penalties: score?.penalties ?? 0))
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .frame(width: columnWidth, alignment: .leading)
        .animation(.snappy, value: total)
    }

    /// "−600", or "—" for the first and while nobody scores, with the penalties that only break
    /// ties after it.
    private func gap(position: Int, total: Int, leaderTotal: Int, penalties: Int) -> String {
        let gap = position == 1 || leaderTotal == 0 ? "—" : formattedMargin(total - leaderTotal)
        return penalties > 0 ? "\(gap) · \(penalties) pen." : gap
    }

    /// Always one line, so that the header keeps its height as points come and go.
    @ViewBuilder
    private var summary: some View {
        if ranking.count > 1 {
            HStack(spacing: 6) {
                summaryContent
            }
            .font(.subheadline.weight(.medium))
            .lineLimit(1)
            .minimumScaleFactor(0.8)
            .frame(width: max(0, viewportWidth - 2 * ComparatorLayout.horizontalPadding))
            // Stays in view while the columns scroll sideways.
            .visualEffect { content, proxy in
                content.offset(
                    x: max(0, ComparatorLayout.horizontalPadding - proxy.frame(in: .scrollView(axis: .horizontal)).minX)
                )
            }
        }
    }

    @ViewBuilder
    private var summaryContent: some View {
        if let first = ranking.first, first.score.total > 0, let firstColla = store.colla(first.collaID) {
            let margin = first.score.total - ranking[1].score.total
            if margin > 0 {
                Image(systemName: "arrowtriangle.up.fill")
                    .foregroundStyle(Color.accentColor)
                Text("\(firstColla.name) guanya per \(formattedMargin(margin))")
            } else {
                Image(systemName: "equal.circle.fill")
                    .foregroundStyle(.orange)
                Text(tieText(winner: firstColla.name, tieBreak: first.tieBreak))
            }
        } else {
            Text("Encara no hi ha castells")
                .foregroundStyle(.secondary)
        }
    }

    private func tieText(winner: String, tieBreak: ComparatorStanding.TieBreak?) -> String {
        switch tieBreak {
        case .penalties: "Empat · guanya \(winner) per menys penalitzacions"
        case .bestCastell: "Empat · guanya \(winner) pel millor castell"
        case .secondCastell: "Empat · guanya \(winner) pel segon castell"
        case nil: "Empat total"
        }
    }
}
#endif
