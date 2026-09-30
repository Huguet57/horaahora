#if os(iOS)
import SwiftUI

/// A manual calculator to compare theoretical performances of up to four colles: "what if"
/// scenarios, each a grid of rounds by colla with steps through the neighbours in points.
public struct ComparatorRootView: View {
    @State private var store: ComparatorStore?
    /// The scenario whose grid is open, over the list.
    @State private var path: [UUID] = []

    public init() {
        let table = try? ScoreTable.bundled()
        _store = State(initialValue: table.map { ComparatorStore(rules: ComparatorRules(table: $0)) })
    }

    public var body: some View {
        NavigationStack(path: $path) {
            if let store {
                ComparatorScenarioList(store: store) { scenario in
                    store.show(scenario)
                    path = [scenario.id]
                }
                .navigationDestination(for: UUID.self) { _ in
                    ComparatorScreen(store: store)
                }
            } else {
                ContentUnavailableView(
                    "No s'ha pogut obrir la taula",
                    systemImage: "exclamationmark.triangle"
                )
            }
        }
    }
}

private struct CollaTarget: Identifiable {
    var id: String { collaID?.uuidString ?? "new" }
    /// `nil` adds a new colla.
    let collaID: UUID?
}

struct ComparatorScreen: View {
    @Bindable var store: ComparatorStore
    @State private var collaTarget: CollaTarget?
    @State private var confirmsClear = false
    @State private var renaming: ComparatorScenario?
    /// The cell whose result picker is open.
    @State private var outcomeTarget: ComparatorCell?
    /// How much of the grid the castell modal covers, beyond the tab bar.
    @State private var sheetCover: CGFloat = 0
    @State private var viewportWidth: CGFloat = 402
    /// A fresh copy shows as a placeholder for a moment, as it looks just like the original.
    @State private var revealsCopy = false

    var body: some View {
        let scenario = store.current
        let ranking = store.rules.ranking(scenario.colles)
        let columnWidth = ComparatorLayout.columnWidth(viewport: viewportWidth, colles: scenario.colles.count)
        ScrollViewReader { proxy in
        ScrollView {
            VStack(spacing: 0) {
                // The header and the grid scroll sideways together once the columns no longer fit.
                ScrollView(.horizontal) {
                    VStack(alignment: .leading, spacing: 12) {
                        ComparatorHeader(
                            store: store,
                            ranking: ranking,
                            onEditColla: { collaTarget = CollaTarget(collaID: $0) },
                            columnWidth: columnWidth,
                            viewportWidth: viewportWidth
                        )
                        ComparatorGrid(
                            store: store,
                            ranking: ranking,
                            columnWidth: columnWidth,
                            onTap: { cell in
                                withAnimation(.snappy(duration: 0.2)) {
                                    store.selection = store.selection == cell ? nil : cell
                                }
                            },
                            onTapOutcome: { outcomeTarget = $0 }
                        )
                    }
                    .padding(.horizontal, ComparatorLayout.horizontalPadding)
                    .padding(.top, 4)
                    .duplicateSkeleton(revealsCopy)
                }
                .scrollIndicators(.hidden)
                .scrollBounceBehavior(.basedOnSize, axes: .horizontal)

                Text("Compten les 3 millors construccions, amb un màxim de 2 carregats. Les penalitzacions només desempaten.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
            }
        }
        .scrollDismissesKeyboard(.immediately)
        // The rows under the castell modal can still scroll into view.
        .safeAreaPadding(.bottom, store.selection == nil ? 0 : sheetCover)
        .onChange(of: store.selection) { _, cell in
            guard let cell else { return }
            withAnimation(.snappy) { proxy.scrollTo(cell.id) }
        }
        }
        .onGeometryChange(for: CGFloat.self) { $0.size.width } action: { width in
            viewportWidth = width
        }
        .onGeometryChange(for: CGFloat.self) { geometry in
            let screenHeight = geometry.size.height + geometry.safeAreaInsets.top + geometry.safeAreaInsets.bottom
            return max(0, screenHeight * 0.45 - geometry.safeAreaInsets.bottom)
        } action: { cover in
            sheetCover = cover
        }
        .background(Color(.systemGroupedBackground))
        .sheet(isPresented: Binding(
            get: { store.selection != nil },
            set: { if !$0 { store.selection = nil } }
        )) {
            if let cell = store.selection {
                ComparatorCastellSheet(store: store, cell: cell)
                    .presentationDetents([ComparatorCastellSheet.detent, .large])
                    .presentationDragIndicator(.visible)
            }
        }
        .navigationTitle(scenario.name ?? "")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { toolbar }
        .scenarioRenameAlert(store: store, scenario: $renaming)
        .onDisappear { store.selection = nil }
        .task(id: revealsCopy) {
            guard revealsCopy else { return }
            try? await Task.sleep(for: duplicateSkeletonDuration)
            withAnimation(.easeOut(duration: 0.25)) { revealsCopy = false }
        }
        .sheet(item: $outcomeTarget) { cell in
            ComparatorOutcomeSheet(store: store, cell: cell)
                .presentationDetents([.height(270)])
                .presentationDragIndicator(.visible)
        }
        .sheet(item: $collaTarget) { target in
            ComparatorCollaPicker(store: store, collaID: target.collaID)
                .presentationDetents([.medium, .large])
        }
        .confirmationDialog("Buidar totes les rondes d'aquest escenari?", isPresented: $confirmsClear, titleVisibility: .visible) {
            Button("Buida", role: .destructive) { store.clearCurrent() }
        }
    }

    @ToolbarContentBuilder
    private var toolbar: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Menu {
                Button("Reanomena", systemImage: "pencil") {
                    renaming = store.current
                }
                Button("Duplica l'escenari", systemImage: "plus.square.on.square") {
                    store.duplicateCurrent()
                    revealsCopy = true
                }
                if store.current.colles.count < ComparatorStore.maxColles {
                    Button("Afegeix una colla", systemImage: "person.badge.plus") {
                        collaTarget = CollaTarget(collaID: nil)
                    }
                }
                Divider()
                Button("Buida les rondes", systemImage: "eraser", role: .destructive) {
                    confirmsClear = true
                }
            } label: {
                Image(systemName: "ellipsis.circle")
            }
            .accessibilityLabel("Més opcions")
        }
    }
}
#endif
