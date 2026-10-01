#if os(iOS)
import SwiftUI

/// Picks the colla for a column, or a new column. What is typed filters the colles, or adds one
/// that is not among them.
struct ComparatorCollaPicker: View {
    let store: ComparatorStore
    /// `nil` adds a new colla.
    let collaID: UUID?

    @Environment(\.dismiss) private var dismiss
    @State private var customName = ""

    var body: some View {
        let taken = Set(store.current.colles.map(\.name))
        NavigationStack {
            List {
                Section {
                    HStack {
                        TextField("Cerca o escriu una colla", text: $customName)
                            .submitLabel(.done)
                            .onSubmit(pickCustom)
                        Button("Afegeix", action: pickCustom)
                            .disabled(customName.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }
                collaSection("Concurs de castells", KnownColla.matching(customName, in: KnownColla.contest), taken: taken)
                collaSection("Altres colles", KnownColla.matching(customName, in: KnownColla.others), taken: taken)
            }
            .navigationTitle(collaID == nil ? "Afegeix una colla" : "Canvia la colla")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel·la") { dismiss() }
                }
            }
        }
    }

    @ViewBuilder
    private func collaSection(_ title: String, _ colles: [KnownColla], taken: Set<String>) -> some View {
        if !colles.isEmpty {
            Section(title) {
                ForEach(colles) { known in
                    Button {
                        pick(known)
                    } label: {
                        HStack {
                            Text(known.name).foregroundStyle(.primary)
                            Spacer()
                            Text(known.shortName)
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                    }
                    .tint(.primary)
                    .disabled(taken.contains(known.name))
                }
            }
        }
    }

    private func pickCustom() {
        let name = customName.trimmingCharacters(in: .whitespaces)
        guard !name.isEmpty else { return }
        if let known = KnownColla.named(name) {
            if !store.current.colles.contains(where: { $0.name == known.name }) { pick(known) }
            return
        }
        let short = String(name.split(separator: " ").last ?? Substring(name)).prefix(5).uppercased()
        pick(KnownColla(name: name, shortName: short))
    }

    private func pick(_ known: KnownColla) {
        if let collaID {
            store.replaceColla(collaID, with: known)
        } else {
            store.addColla(known)
        }
        dismiss()
    }
}

#endif
