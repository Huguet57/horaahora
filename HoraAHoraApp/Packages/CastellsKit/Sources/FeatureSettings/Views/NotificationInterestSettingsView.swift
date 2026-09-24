import SwiftUI
import CastellsDomain

struct NotificationInterestSettingsView: View {
    let model: SettingsModel
    let hasFollowedGroups: Bool
    let onChooseGroups: () -> Void

    var body: some View {
        List {
            Section {
                ForEach(NotificationInterestLevel.allCases, id: \.self) { level in
                    interestRow(level)
                }
            } header: {
                Text("Quines notícies vols rebre?")
                    .font(.headline)
                    .foregroundStyle(.primary)
                    .textCase(nil)
                    .padding(.bottom, 8)
            }

            Section {
                Button(action: onChooseGroups) {
                    HStack {
                        Text("Tria les colles a l’Agenda")
                        Spacer(minLength: 12)
                        Image(systemName: "chevron.forward")
                            .font(.footnote.weight(.semibold))
                            .foregroundStyle(.tertiary)
                            .accessibilityHidden(true)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityHint("Obre el selector de colles de l’Agenda")
            } header: {
                Text("Les teves colles")
            } footer: {
                Text(hasFollowedGroups
                    ? "Fem servir les mateixes colles que segueixes a l’Agenda."
                    : "Tria les teves colles per personalitzar els avisos. Ara es té en compte l’actualitat general.")
            }
        }
        .settingsListStyle()
        .navigationTitle("Notícies")
        .settingsInlineNavigationTitle()
    }

    private func interestRow(_ level: NotificationInterestLevel) -> some View {
        Button {
            Task { await model.setMinimumInterest(level) }
        } label: {
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(level.settingsTitle)
                        .foregroundStyle(.primary)
                    Text(level.settingsDescription)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer(minLength: 0)
                Image(systemName: "checkmark")
                    .font(.body.weight(.semibold))
                    .foregroundStyle(Color.accentColor)
                    .opacity(model.minimumInterest == level ? 1 : 0)
                    .accessibilityHidden(true)
            }
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(model.notificationStatus == .loading)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(model.minimumInterest == level ? .isSelected : [])
    }
}

extension NotificationInterestLevel {
    var settingsTitle: String {
        switch self {
        case .low: "Totes"
        case .medium: "Rellevants"
        case .high: "Destacades"
        }
    }

    var settingsDescription: String {
        switch self {
        case .low: "Totes les notícies que publiquem."
        case .medium: "Totes les notícies de les teves colles i l’actualitat interessant."
        case .high: "Notícies excepcionals i novetats interessants de les teves colles."
        }
    }
}
