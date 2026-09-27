import SwiftUI

/// The official score table, from the castell worth the most to the one worth the least.
///
/// The bars zoom to the rows on screen: the smallest value there starts near the left and the
/// largest fills the width, so that neighbouring castells compare at a glance. Tapping a castell
/// marks the ones below it whose descarregat beats its carregat.
public struct ScoreTableRootView: View {
    private let table: ScoreTable?
    @State private var scale: ScoreBarScale?
    @State private var selectedNotation: String?

    public init() {
        let table = try? ScoreTable.bundled()
        self.table = table
        _scale = State(initialValue: table.map(ScoreBarScale.init(table:)))
    }

    public var body: some View {
        NavigationStack {
            Group {
                if let table, let scale {
                    tableView(table, scale: scale)
                } else {
                    ContentUnavailableView(
                        "No s'ha pogut obrir la taula",
                        systemImage: "exclamationmark.triangle"
                    )
                }
            }
            .navigationTitle("Puntuacions")
            .scoreTableLargeNavigationTitle()
        }
    }

    private func tableView(_ table: ScoreTable, scale: ScoreBarScale) -> some View {
        let selected = table.castells.first { $0.notation == selectedNotation }
        let winners = Set(selected.map { table.notationsBelowWhoseUnloadedBeats(loadedOf: $0) } ?? [])
        return ScrollView {
            LazyVStack(alignment: .leading, spacing: 0, pinnedViews: [.sectionHeaders]) {
                ForEach(table.sectionsByPoints) { section in
                    Section {
                        ForEach(section.castells) { castell in
                            ScoreTableRow(
                                castell: castell,
                                scale: scale,
                                highlight: castell.notation == selectedNotation
                                    ? .selected
                                    : winners.contains(castell.notation)
                                        ? .beatsSelectedLoaded(selected?.notation ?? "")
                                        : .none
                            ) {
                                selectedNotation = castell.notation == selectedNotation
                                    ? nil
                                    : castell.notation
                            }
                        }
                    } header: {
                        ScoreTableSectionHeader(group: section.group)
                            .onGeometryChange(for: CGFloat.self) { proxy in
                                proxy.size.height
                            } action: { height in
                                scale.setPinnedHeaderHeight(height)
                            }
                    }
                }

                Text("Taula oficial de puntuacions del Concurs de Castells 2026.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
            }
        }
        // The scroll view's own frame already leaves out the navigation and tab bars, which the
        // rows only pass under.
        .onGeometryChange(for: CGRect.self) { proxy in
            proxy.frame(in: .global)
        } action: { viewport in
            scale.setViewport(viewport)
        }
    }
}

private extension View {
    @ViewBuilder
    func scoreTableLargeNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.large)
        #else
        self
        #endif
    }
}
