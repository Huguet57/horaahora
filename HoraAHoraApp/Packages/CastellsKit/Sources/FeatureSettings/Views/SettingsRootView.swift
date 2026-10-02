import SwiftUI
import CastellsDomain

/// Ajustos: privacy, help and the app with the sources of its data.
public struct SettingsRootView: View {
    @Bindable private var model: SettingsModel
    @State private var identifierWasCopied = false

    private let configuration: SettingsConfiguration
    private let onOpenURL: (URL) -> Void
    private let onContactSupport: (URL) -> Void
    private let onCopyIdentifier: (String) -> Void

    public init(
        model: SettingsModel,
        configuration: SettingsConfiguration,
        onOpenURL: @escaping (URL) -> Void,
        onContactSupport: @escaping (URL) -> Void,
        onCopyIdentifier: @escaping (String) -> Void
    ) {
        self.model = model
        self.configuration = configuration
        self.onOpenURL = onOpenURL
        self.onContactSupport = onContactSupport
        self.onCopyIdentifier = onCopyIdentifier
    }

    public var body: some View {
        NavigationStack {
            List {
                privacySection
                helpSection
                aboutSection
            }
            .settingsListStyle()
            .navigationTitle("Ajustos")
            .settingsLargeNavigationTitle()
            .task {
                model.refreshConversationSharing()
            }
        }
    }

    private var privacySection: some View {
        Section {
            if model.showsConversationSharing {
                Toggle(isOn: conversationSharingBinding) {
                    Label("Millora la calculadora", systemImage: "text.bubble")
                }
            }
            Button { onOpenURL(configuration.privacyURL) } label: {
                SettingsLinkLabel(title: "Política de privacitat", systemImage: "hand.raised")
            }
            .buttonStyle(.plain)
        } header: {
            Text("Privacitat i dades")
        } footer: {
            if model.showsConversationSharing {
                Text(
                    "Desa durant 90 dies les converses noves de la calculadora, sense cap identificador del dispositiu, per detectar errors i millorar les respostes."
                )
            }
        }
    }

    private var helpSection: some View {
        Section("Ajuda") {
            Button { onContactSupport(configuration.supportEmailURL) } label: {
                SettingsLinkLabel(title: "Contacta amb suport", systemImage: "envelope")
            }
            .buttonStyle(.plain)

            Button {
                onCopyIdentifier(configuration.technicalIdentifier)
                identifierWasCopied = true
            } label: {
                HStack(spacing: 12) {
                    Image(systemName: identifierWasCopied ? "checkmark.circle.fill" : "doc.on.doc")
                        .foregroundStyle(identifierWasCopied ? Color.green : Color.accentColor)
                        .accessibilityHidden(true)
                    VStack(alignment: .leading, spacing: 3) {
                        Text(identifierWasCopied ? "Identificador copiat" : "Copia l'identificador")
                            .foregroundStyle(.primary)
                        Text(configuration.technicalIdentifier)
                            .font(.caption.monospaced())
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(
                identifierWasCopied
                    ? "Identificador tècnic copiat"
                    : "Copia l'identificador tècnic complet"
            )
            .accessibilityValue(configuration.technicalIdentifier)
            .task(id: identifierWasCopied) {
                guard identifierWasCopied else { return }
                try? await Task.sleep(for: .seconds(2))
                identifierWasCopied = false
            }
        }
    }

    private var aboutSection: some View {
        Section("Sobre \(configuration.appName)") {
            versionRow

            NavigationLink {
                SourcesAndCreditsView(credits: configuration.credits, onOpenURL: onOpenURL)
            } label: {
                Label("Fonts i crèdits", systemImage: "text.book.closed")
            }
        }
    }

    private var versionRow: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(configuration.appName).font(.headline)
            Text(configuration.versionAndBuild)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 5)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }

    private var conversationSharingBinding: Binding<Bool> {
        Binding(
            get: { model.isConversationSharingEnabled },
            set: { model.setConversationSharingEnabled($0) }
        )
    }
}
