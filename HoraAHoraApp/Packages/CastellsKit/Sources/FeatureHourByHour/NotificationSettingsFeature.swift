import Observation
import SwiftUI

public enum HourByHourNotificationStatus: Equatable, Sendable {
    case loading
    case notDetermined
    case enabled
    case disabled
    case denied
}

@MainActor
public protocol HourByHourNotificationManaging: AnyObject {
    func currentStatus() async -> HourByHourNotificationStatus
    func enable() async throws -> HourByHourNotificationStatus
    func disable() async throws -> HourByHourNotificationStatus
    func openSystemSettings() async
}

@MainActor
@Observable
public final class HourByHourNotificationSettingsModel {
    public private(set) var status: HourByHourNotificationStatus = .loading
    public private(set) var isUpdating = false
    public private(set) var errorMessage: String?

    private let manager: any HourByHourNotificationManaging

    public init(manager: any HourByHourNotificationManaging) {
        self.manager = manager
    }

    public func refresh() async {
        status = await manager.currentStatus()
    }

    public func setEnabled(_ enabled: Bool) async {
        guard !isUpdating else { return }
        isUpdating = true
        errorMessage = nil
        defer { isUpdating = false }

        do {
            status = try await enabled ? manager.enable() : manager.disable()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func openSystemSettings() async {
        await manager.openSystemSettings()
    }
}

struct HourByHourNotificationSettingsView: View {
    @Bindable var model: HourByHourNotificationSettingsModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(spacing: 14) {
                        Image(systemName: "bell.badge.fill")
                            .font(.system(size: 42))
                            .foregroundStyle(.tint)
                            .accessibilityHidden(true)

                        Text("No et perdis cap novetat")
                            .font(.title2.bold())
                            .multilineTextAlignment(.center)

                        Text("Rep un avís quan hi hagi una entrada nova a l'Hora a Hora. Ho pots canviar sempre des d'aquí.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                }

                Section {
                    if model.status == .denied {
                        LabeledContent {
                            Text("Desactivades")
                                .foregroundStyle(.secondary)
                        } label: {
                            Label("Hora a Hora", systemImage: "bell.slash.fill")
                        }

                        Button("Obre els ajustos de l'iPhone") {
                            Task { await model.openSystemSettings() }
                        }
                    } else {
                        Toggle(isOn: enabledBinding) {
                            Label("Hora a Hora", systemImage: statusSystemImage)
                        }
                        .disabled(model.status == .loading || model.isUpdating)
                    }

                    HStack(spacing: 8) {
                        if model.status == .loading || model.isUpdating {
                            ProgressView()
                                .controlSize(.small)
                        } else {
                            Image(systemName: statusSystemImage)
                                .foregroundStyle(statusColor)
                        }
                        Text(statusText)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Notificacions")
                } footer: {
                    Text(footerText)
                }

                if let errorMessage = model.errorMessage {
                    Section {
                        Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Configuració")
            .notificationSettingsInlineNavigationTitle()
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fet") { dismiss() }
                }
            }
            .task { await model.refresh() }
            .onChange(of: scenePhase) { _, phase in
                guard phase == .active else { return }
                Task { await model.refresh() }
            }
        }
    }

    private var enabledBinding: Binding<Bool> {
        Binding(
            get: { model.status == .enabled },
            set: { isEnabled in
                Task { await model.setEnabled(isEnabled) }
            }
        )
    }

    private var statusText: String {
        switch model.status {
        case .loading:
            "Comprovant l'estat…"
        case .notDetermined:
            "Encara no les has configurat. iOS et demanarà permís en activar-les."
        case .enabled:
            "Activades en aquest dispositiu."
        case .disabled:
            "Desactivades des de l'app."
        case .denied:
            "El permís està bloquejat als ajustos de l'iPhone."
        }
    }

    private var footerText: String {
        if model.status == .denied {
            "Apple només permet recuperar un permís denegat des dels ajustos del sistema."
        } else {
            "El permís d'iOS només apareix després que decideixis activar les notificacions."
        }
    }

    private var statusSystemImage: String {
        switch model.status {
        case .enabled:
            "bell.fill"
        case .loading, .notDetermined, .disabled, .denied:
            "bell.slash"
        }
    }

    private var statusColor: Color {
        switch model.status {
        case .enabled:
            .green
        case .denied:
            .orange
        case .loading, .notDetermined, .disabled:
            .secondary
        }
    }
}

private extension View {
    @ViewBuilder
    func notificationSettingsInlineNavigationTitle() -> some View {
        #if os(iOS)
        navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }
}

struct HourByHourNotificationOnboardingCard: View {
    let onConfigure: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "bell.badge.fill")
                .font(.title2)
                .foregroundStyle(.tint)
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 5) {
                Text("Vols rebre les novetats?")
                    .font(.headline)
                Text("Activa els avisos de l'Hora a Hora quan tu vulguis.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button("Configura-ho") { onConfigure() }
                    .font(.subheadline.weight(.semibold))
                    .padding(.top, 2)
            }

            Spacer(minLength: 0)

            Button(action: onDismiss) {
                Image(systemName: "xmark")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)
                    .padding(6)
            }
            .accessibilityLabel("Ara no")
        }
        .padding(14)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}
