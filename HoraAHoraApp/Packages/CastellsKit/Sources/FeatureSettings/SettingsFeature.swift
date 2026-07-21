import SwiftUI

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
                notificationSection
                privacySection
                helpSection
                aboutSection
            }
            .settingsListStyle()
            .navigationTitle("Ajustos")
            .settingsLargeNavigationTitle()
            .task { await model.refreshNotificationStatus() }
        }
    }

    private var notificationSection: some View {
        Section("Notificacions") {
            Toggle(isOn: notificationsEnabledBinding) {
                Label("Hora a Hora", systemImage: "bell")
            }
            .disabled(
                model.notificationStatus == .loading
                    || model.notificationStatus == .denied
                    || model.isUpdatingNotifications
            )

            if model.notificationStatus == .denied {
                Label("Bloquejades per iOS", systemImage: "exclamationmark.triangle.fill")
                    .font(.footnote)
                    .foregroundStyle(.orange)

                Button("Obre els ajustos de l'iPhone") {
                    Task { await model.openSystemSettings() }
                }
            }

            if let errorMessage = model.notificationErrorMessage {
                Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
            }
        }
    }

    private var privacySection: some View {
        Section("Privacitat i dades") {
            Button {
                onOpenURL(configuration.privacyURL)
            } label: {
                SettingsLinkLabel(
                    title: "Política de privacitat",
                    systemImage: "hand.raised"
                )
            }
            .buttonStyle(.plain)
        }
    }

    private var helpSection: some View {
        Section("Ajuda") {
            Button {
                onContactSupport(configuration.supportEmailURL)
            } label: {
                SettingsLinkLabel(
                    title: "Contacta amb suport",
                    systemImage: "envelope"
                )
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
            VStack(alignment: .leading, spacing: 3) {
                Text(configuration.appName)
                    .font(.headline)
                Text(configuration.versionAndBuild)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding(.vertical, 5)
            .accessibilityElement(children: .combine)

            NavigationLink {
                SourcesAndCreditsView(
                    configuration: configuration,
                    onOpenURL: onOpenURL
                )
            } label: {
                Label("Fonts i crèdits", systemImage: "text.book.closed")
            }
        }
    }

    private var notificationsEnabledBinding: Binding<Bool> {
        Binding(
            get: { model.notificationStatus == .enabled },
            set: { enabled in
                Task { await model.setHourByHourNotificationsEnabled(enabled) }
            }
        )
    }

}

private struct SourcesAndCreditsView: View {
    let configuration: SettingsConfiguration
    let onOpenURL: (URL) -> Void

    var body: some View {
        List {
            Section {
                creditRow(
                    name: "Revista Castells",
                    detail: "Font de l'Hora a Hora",
                    url: configuration.revistaCastellsURL
                )
                creditRow(
                    name: "Coordinadora de Colles Castelleres de Catalunya (CCCC)",
                    detail: "Font de l'Agenda",
                    url: configuration.ccccAgendaURL
                )
                creditRow(
                    name: "Taula oficial del Concurs de Castells 2026",
                    detail: "Font de la Calculadora",
                    url: configuration.concursCastellsURL
                )
            } footer: {
                Text("Aquestes atribucions identifiquen les fonts de les dades i no impliquen cap col·laboració formal.")
            }
        }
        .settingsListStyle()
        .navigationTitle("Fonts i crèdits")
        .settingsInlineNavigationTitle()
    }

    @ViewBuilder
    private func creditRow(name: String, detail: String, url: URL?) -> some View {
        if let url {
            Button {
                onOpenURL(url)
            } label: {
                HStack(alignment: .center, spacing: 12) {
                    creditText(name: name, detail: detail)
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
            creditText(name: name, detail: detail)
        }
    }

    private func creditText(name: String, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(name)
                .foregroundStyle(.primary)
            Text(detail)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }
}

private struct SettingsLinkLabel: View {
    let title: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 12) {
            Label(title, systemImage: systemImage)
                .foregroundStyle(.primary)
            Spacer(minLength: 12)
            Image(systemName: "arrow.up.right")
                .font(.caption)
                .foregroundStyle(.tertiary)
                .accessibilityHidden(true)
        }
    }
}

private extension View {
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
