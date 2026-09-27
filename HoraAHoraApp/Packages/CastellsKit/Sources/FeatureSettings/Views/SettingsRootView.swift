import SwiftUI
import CastellsDomain

/// Ajustos: privacy, help and the app with the sources of its data.
///
/// An app can add its own sections at the top (`leadingSections`), more sources
/// (`additionalCredits`) and a handler for taps on the version row (`onVersionTap`), which
/// returns what the row says for a moment, or nil.
public struct SettingsRootView<LeadingSections: View>: View {
    @Bindable private var model: SettingsModel
    @State private var identifierWasCopied = false
    @State private var versionMessage: String?

    private let configuration: SettingsConfiguration
    private let additionalCredits: [SettingsCredit]
    private let onVersionTap: (@MainActor () -> String?)?
    private let onOpenURL: (URL) -> Void
    private let onContactSupport: (URL) -> Void
    private let onCopyIdentifier: (String) -> Void
    private let leadingSections: LeadingSections

    public init(
        model: SettingsModel,
        configuration: SettingsConfiguration,
        additionalCredits: [SettingsCredit] = [],
        onVersionTap: (@MainActor () -> String?)? = nil,
        onOpenURL: @escaping (URL) -> Void,
        onContactSupport: @escaping (URL) -> Void,
        onCopyIdentifier: @escaping (String) -> Void,
        @ViewBuilder leadingSections: () -> LeadingSections
    ) {
        self.model = model
        self.configuration = configuration
        self.additionalCredits = additionalCredits
        self.onVersionTap = onVersionTap
        self.onOpenURL = onOpenURL
        self.onContactSupport = onContactSupport
        self.onCopyIdentifier = onCopyIdentifier
        self.leadingSections = leadingSections()
    }

    public var body: some View {
        NavigationStack {
            List {
                leadingSections
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
                SourcesAndCreditsView(
                    credits: configuration.credits + additionalCredits,
                    onOpenURL: onOpenURL
                )
            } label: {
                Label("Fonts i crèdits", systemImage: "text.book.closed")
            }
        }
    }

    /// The app and its version. Taps only do something when the app handles them.
    @ViewBuilder
    private var versionRow: some View {
        if let onVersionTap {
            versionLabel
                .contentShape(Rectangle())
                .onTapGesture {
                    guard let message = onVersionTap() else { return }
                    versionMessage = message
                }
                .sensoryFeedback(.success, trigger: versionMessage) { _, message in message != nil }
                .task(id: versionMessage) {
                    guard versionMessage != nil else { return }
                    try? await Task.sleep(for: .seconds(2))
                    versionMessage = nil
                }
                .accessibilityElement(children: .combine)
        } else {
            versionLabel
                .accessibilityElement(children: .combine)
        }
    }

    private var versionLabel: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(configuration.appName).font(.headline)
            Text(versionMessage ?? configuration.versionAndBuild)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 5)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var conversationSharingBinding: Binding<Bool> {
        Binding(
            get: { model.isConversationSharingEnabled },
            set: { model.setConversationSharingEnabled($0) }
        )
    }
}

extension SettingsRootView where LeadingSections == EmptyView {
    /// Ajustos as the public app shows it: the calculator's settings only.
    public init(
        model: SettingsModel,
        configuration: SettingsConfiguration,
        onOpenURL: @escaping (URL) -> Void,
        onContactSupport: @escaping (URL) -> Void,
        onCopyIdentifier: @escaping (String) -> Void
    ) {
        self.init(
            model: model,
            configuration: configuration,
            onOpenURL: onOpenURL,
            onContactSupport: onContactSupport,
            onCopyIdentifier: onCopyIdentifier
        ) {
            EmptyView()
        }
    }
}
