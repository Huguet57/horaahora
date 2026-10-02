import SwiftUI

struct SourcesAndCreditsView: View {
    let credits: [SettingsCredit]
    let onOpenURL: (URL) -> Void

    var body: some View {
        List {
            Section {
                ForEach(credits, id: \.name) { credit in
                    creditRow(credit)
                }
            } footer: {
                Text(
                    "Aquestes atribucions identifiquen les fonts de les dades i no impliquen cap col·laboració formal."
                )
            }
        }
        .settingsListStyle()
        .navigationTitle("Fonts i crèdits")
        .settingsInlineNavigationTitle()
    }

    @ViewBuilder
    private func creditRow(_ credit: SettingsCredit) -> some View {
        if let url = credit.url {
            Button { onOpenURL(url) } label: {
                HStack(alignment: .center, spacing: 12) {
                    creditText(credit)
                    Spacer(minLength: 12)
                    Image(systemName: "arrow.up.right")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                        .accessibilityHidden(true)
                }
            }
            .buttonStyle(.plain)
            .accessibilityHint("Obre el web oficial")
        } else {
            creditText(credit)
        }
    }

    private func creditText(_ credit: SettingsCredit) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(credit.name).foregroundStyle(.primary)
            Text(credit.detail).font(.subheadline).foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }
}

struct SettingsLinkLabel: View {
    let title: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 12) {
            Label(title, systemImage: systemImage).foregroundStyle(.primary)
            Spacer(minLength: 12)
            Image(systemName: "arrow.up.right")
                .font(.caption)
                .foregroundStyle(.tertiary)
                .accessibilityHidden(true)
        }
    }
}

/// The look of the settings pages.
extension View {
    @ViewBuilder
    func settingsListStyle() -> some View {
        #if os(iOS)
        listStyle(.insetGrouped)
        #else
        self
        #endif
    }

    @ViewBuilder
    func settingsLargeNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.large)
        #else
        self
        #endif
    }

    @ViewBuilder
    func settingsInlineNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }
}
