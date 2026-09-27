import SwiftUI
import CastellsDomain

/// The news notifications at the top of Ajustos: on or off, and which news they bring.
struct NotificationSettingsSection: View {
    let model: InternalSettingsModel
    let hasFollowedGroups: Bool
    let onChooseGroups: () -> Void

    var body: some View {
        Section {
            Toggle(isOn: notificationsEnabledBinding) {
                Label("Avisos de notícies", systemImage: "bell")
            }
            .disabled(
                model.notificationStatus == .loading
                    || model.notificationStatus == .denied
                    || model.isUpdatingNotifications
            )

            NavigationLink {
                NotificationInterestSettingsView(
                    model: model,
                    hasFollowedGroups: hasFollowedGroups,
                    onChooseGroups: onChooseGroups
                )
            } label: {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Quines notícies?")
                    Text(model.minimumInterest.settingsTitle)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 2)
            }
            .disabled(model.notificationStatus == .loading)

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
        } header: {
            Text("Notificacions")
        } footer: {
            if model.notificationStatus == .notDetermined || model.notificationStatus == .disabled {
                Text("Pots triar què rebràs abans d’activar els avisos.")
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
