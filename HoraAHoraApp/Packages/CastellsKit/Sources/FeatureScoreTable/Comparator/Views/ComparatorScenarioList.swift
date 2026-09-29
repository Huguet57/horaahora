#if os(iOS)
import SwiftUI

/// The comparator's main page: every scenario as its score and each colla's castells, the
/// favourites pinned on top. Tapping one opens its grid; dragging it reorders it within its
/// section; its menu pins, renames, duplicates or deletes it.
struct ComparatorScenarioList: View {
    let store: ComparatorStore
    let onOpen: (ComparatorScenario) -> Void

    @State private var deleting: ComparatorScenario?
    @State private var renaming: ComparatorScenario?

    var body: some View {
        List {
            if !store.favorites.isEmpty {
                Section("Favorits") {
                    rows(store.favorites)
                        .onMove { store.moveScenarios(favorites: true, from: $0, to: $1) }
                }
            }
            Section {
                rows(store.others)
                    .onMove { store.moveScenarios(favorites: false, from: $0, to: $1) }
            } header: {
                if !store.favorites.isEmpty { Text("Escenaris") }
            } footer: {
                Text("Mantén premut un escenari per moure'l. Duplica'n un per provar què passa si una colla fa un altre castell.")
            }
        }
        .animation(.snappy, value: store.scenarios.map(\.id))
        .navigationTitle("Comparador")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                EditButton()
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button("Nou escenari", systemImage: "plus") {
                    onOpen(store.addEmptyScenario())
                }
            }
        }
        .scenarioRenameAlert(store: store, scenario: $renaming)
        .confirmationDialog(
            "Eliminar aquest escenari?",
            isPresented: Binding(get: { deleting != nil }, set: { if !$0 { deleting = nil } }),
            titleVisibility: .visible
        ) {
            Button("Elimina", role: .destructive) {
                if let deleting { store.delete(deleting) }
                deleting = nil
            }
        }
    }

    private func rows(_ scenarios: [ComparatorScenario]) -> some DynamicViewContent {
        ForEach(scenarios) { scenario in
            row(scenario)
                .swipeActions {
                    if store.scenarios.count > 1 {
                        Button("Elimina", systemImage: "trash", role: .destructive) {
                            deleting = scenario
                        }
                    }
                    Button("Duplica", systemImage: "plus.square.on.square") {
                        store.duplicate(scenario)
                    }
                    .tint(.gray)
                }
                .swipeActions(edge: .leading) {
                    Button(
                        scenario.isFavorite ? "Treu de favorits" : "Favorit",
                        systemImage: scenario.isFavorite ? "star.slash" : "star"
                    ) {
                        store.toggleFavorite(scenario)
                    }
                    .tint(.yellow)
                }
        }
    }

    private func row(_ scenario: ComparatorScenario) -> some View {
        let summary = store.rules.summary(of: scenario)
        return HStack(alignment: .center, spacing: 8) {
            Button {
                onOpen(scenario)
            } label: {
                VStack(alignment: .leading, spacing: 6) {
                    if let name = scenario.name {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(name)
                                .font(.headline)
                                .lineLimit(2)
                            Text(summary.title)
                                .font(.subheadline.weight(.semibold).monospacedDigit())
                                .foregroundStyle(.secondary)
                        }
                    } else {
                        Text(summary.title)
                            .font(.headline.monospacedDigit())
                            .lineLimit(2)
                            .minimumScaleFactor(0.8)
                    }
                    VStack(alignment: .leading, spacing: 2) {
                        ForEach(summary.lines, id: \.self) { line in
                            Text(line)
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                                .minimumScaleFactor(0.7)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 4)
                .contentShape(.rect)
            }
            .buttonStyle(.plain)

            Menu {
                Button(
                    scenario.isFavorite ? "Treu de favorits" : "Afegeix a favorits",
                    systemImage: scenario.isFavorite ? "star.slash" : "star"
                ) {
                    store.toggleFavorite(scenario)
                }
                Button("Reanomena", systemImage: "pencil") {
                    renaming = scenario
                }
                Button("Duplica", systemImage: "plus.square.on.square") {
                    store.duplicate(scenario)
                }
                if store.scenarios.count > 1 {
                    Button("Elimina", systemImage: "trash", role: .destructive) {
                        deleting = scenario
                    }
                }
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
                    .frame(width: 36, height: 44)
                    .contentShape(.rect)
            }
            .buttonStyle(.borderless)
            .tint(.secondary)
            .accessibilityLabel("Opcions de l'escenari")
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel([scenario.name, summary.title].compactMap { $0 }.joined(separator: ", "))
    }
}

extension View {
    /// Asks for a new name for `scenario` while there is one; a blank name clears it.
    func scenarioRenameAlert(store: ComparatorStore, scenario: Binding<ComparatorScenario?>) -> some View {
        modifier(ScenarioRenameAlert(store: store, scenario: scenario))
    }
}

private struct ScenarioRenameAlert: ViewModifier {
    let store: ComparatorStore
    @Binding var scenario: ComparatorScenario?
    @State private var name = ""

    func body(content: Content) -> some View {
        content
            .alert("Nom de l'escenari", isPresented: Binding(
                get: { scenario != nil },
                set: { if !$0 { scenario = nil } }
            )) {
                TextField(scenario.map { store.rules.summary(of: $0).title } ?? "Nom", text: $name)
                Button("Desa") {
                    if let scenario { store.rename(scenario, to: name) }
                    scenario = nil
                }
                Button("Cancel·la", role: .cancel) { scenario = nil }
            } message: {
                Text("Deixa'l buit per mostrar qui guanya.")
            }
            .onChange(of: scenario?.id) { _, _ in name = scenario?.name ?? "" }
    }
}
#endif
