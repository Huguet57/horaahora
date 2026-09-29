#if os(iOS)
import SwiftUI

/// Picks the colla for a column, or a new column.
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
                        TextField("Una altra colla", text: $customName)
                            .submitLabel(.done)
                            .onSubmit(pickCustom)
                        Button("Afegeix", action: pickCustom)
                            .disabled(customName.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }
                Section("Colles") {
                    ForEach(KnownColla.all) { known in
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
            .navigationTitle(collaID == nil ? "Afegeix una colla" : "Canvia la colla")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel·la") { dismiss() }
                }
            }
        }
    }

    private func pickCustom() {
        let name = customName.trimmingCharacters(in: .whitespaces)
        guard !name.isEmpty else { return }
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
