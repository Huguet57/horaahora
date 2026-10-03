#if os(iOS)
import SwiftUI

/// The modal for the selected cell, in two steps. First every castell by points, centred on the
/// cell's castell or, for an empty cell, near what the colles did; the ones the colla may not
/// try are disabled and say why. Then the result of the picked castell, which puts it in the
/// cell and closes the modal.
struct ComparatorCastellSheet: View {
    static let detent = PresentationDetent.fraction(0.45)
    private static let rowHeight: CGFloat = 34

    let store: ComparatorStore
    let cell: ComparatorCell

    /// The castell picked in the first step, whose result the second step asks for.
    @State private var pickedNotation: String?
    /// A castell without manilles, tapped in the first step and waiting to be confirmed.
    @State private var unlikelyNotation: String?

    /// Castells without manilles that have never been done, each with the one with folre and
    /// manilles it is easily mistaken for.
    static let unlikelyCastells = ["3de10sm": "3de10fm", "4de10sm": "4de10fm"]

    var body: some View {
        if let colla = store.colla(cell.collaID) {
            let castell = colla.rounds[cell.round]
            VStack(spacing: 12) {
                header(colla, castell: castell)
                if let pickedNotation {
                    ComparatorOutcomeGrid(
                        current: castell?.notation == pickedNotation ? castell?.outcome : nil
                    ) { outcome in
                        store.set(PlannedCastell(notation: pickedNotation, outcome: outcome), at: cell)
                        store.selection = nil
                    }
                    .transition(.move(edge: .trailing).combined(with: .opacity))
                    Spacer(minLength: 0)
                } else {
                    ladder(colla, current: castell)
                        .transition(.move(edge: .leading).combined(with: .opacity))
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 18)
            .onChange(of: cell) { _, _ in pickedNotation = nil }
            .alert(
                "\(unlikelyNotation ?? "") sense manilles?",
                isPresented: Binding(
                    get: { unlikelyNotation != nil },
                    set: { if !$0 { unlikelyNotation = nil } }
                ),
                presenting: unlikelyNotation
            ) { notation in
                Button("Sí, \(notation)") { pick(notation) }
                if let alternative = Self.unlikelyCastells[notation] {
                    Button("No, \(alternative)") { pick(alternative) }
                }
                Button("Cancel·la", role: .cancel) {}
            } message: { _ in
                Text("No s'ha fet mai.")
            }
        }
    }

    private func header(_ colla: ComparatorColla, castell: PlannedCastell?) -> some View {
        HStack(spacing: 8) {
            if pickedNotation != nil {
                Button {
                    withAnimation(.snappy(duration: 0.25)) { pickedNotation = nil }
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.body.weight(.semibold))
                        .frame(width: 36, height: 36)
                        .contentShape(.rect)
                }
                .accessibilityLabel("Torna als castells")
            }
            VStack(alignment: .leading, spacing: 1) {
                Text(colla.name)
                    .font(.headline)
                HStack(spacing: 4) {
                    Text("Ronda \(cell.round + 1)")
                    if let pickedNotation {
                        Text("·")
                        Text(pickedNotation)
                            .monospaced()
                            .fontWeight(.semibold)
                            .foregroundStyle(.primary)
                    }
                }
                .font(.subheadline)
                .foregroundStyle(.secondary)
            }
            .lineLimit(1)
            Spacer(minLength: 8)
            Button(role: .destructive) {
                store.set(nil, at: cell)
                store.selection = nil
            } label: {
                Label("Buida", systemImage: "trash")
                    .font(.body.weight(.semibold))
                    .padding(.horizontal, 6)
                    .frame(minHeight: 36)
            }
            .buttonStyle(.bordered)
            .buttonBorderShape(.capsule)
            .tint(.red)
            .disabled(castell == nil)
            .accessibilityLabel("Buida la ronda")
        }
    }

    private func ladder(_ colla: ComparatorColla, current: PlannedCastell?) -> some View {
        let castells = Array(store.rules.ladder(for: .unloaded).reversed())
        return ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 2) {
                    ForEach(castells) { castell in
                        row(
                            castell,
                            isCurrent: castell.notation == current?.notation,
                            restriction: store.rules.restriction(of: castell.notation, inRound: cell.round, for: colla)
                        )
                        .id(castell.notation)
                    }
                }
                // Just enough to clear the fade: the list starts and ends at its first and last
                // castell, with no empty space around them.
                .padding(.vertical, 8)
            }
            .scrollIndicators(.hidden)
            .mask {
                LinearGradient(
                    stops: [
                        .init(color: .clear, location: 0),
                        .init(color: .black, location: 0.04),
                        .init(color: .black, location: 0.96),
                        .init(color: .clear, location: 1),
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            }
            .onAppear { proxy.scrollTo(store.anchor(for: cell), anchor: .center) }
            .onChange(of: cell) { _, cell in
                proxy.scrollTo(store.anchor(for: cell), anchor: .center)
            }
        }
    }

    private func pick(_ notation: String) {
        withAnimation(.snappy(duration: 0.25)) { pickedNotation = notation }
    }

    private func row(_ castell: ScoreTableCastell, isCurrent: Bool, restriction: ComparatorRestriction?) -> some View {
        let isDisabled = restriction != nil && !isCurrent
        return Button {
            if Self.unlikelyCastells[castell.notation] != nil, !isCurrent {
                unlikelyNotation = castell.notation
            } else {
                pick(castell.notation)
            }
        } label: {
            HStack(spacing: 8) {
                Text(castell.notation)
                    .font(.callout.monospaced().weight(isCurrent ? .bold : .regular))
                    .foregroundStyle(isDisabled ? .tertiary : .primary)
                if let restriction {
                    Text(restriction.label)
                        .font(.caption2)
                        .foregroundStyle(isDisabled ? AnyShapeStyle(.tertiary) : AnyShapeStyle(.orange))
                        .lineLimit(1)
                }
                Spacer(minLength: 4)
                Text(formattedPoints(castell.unloaded))
                    .font(.callout.monospacedDigit())
                    .foregroundStyle(isDisabled ? .tertiary : isCurrent ? .primary : .secondary)
            }
            .padding(.horizontal, 10)
            .frame(height: Self.rowHeight)
            .background(isCurrent ? Color.accentColor.opacity(0.16) : .clear, in: .rect(cornerRadius: 8))
            .contentShape(.rect)
        }
        .buttonStyle(.plain)
        .disabled(isDisabled)
    }
}
#endif
