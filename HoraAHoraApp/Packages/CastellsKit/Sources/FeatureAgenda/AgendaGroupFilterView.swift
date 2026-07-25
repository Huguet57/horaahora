import SwiftUI
#if os(iOS)
import UIKit
#elseif os(macOS)
import AppKit
#endif

#if os(iOS)
private let agendaGroupFilterBackground = Color(uiColor: .systemGroupedBackground)
#else
private let agendaGroupFilterBackground = Color(nsColor: .windowBackgroundColor)
#endif

struct AgendaGroupFilterView: View {
    let model: AgendaViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""

    var body: some View {
        NavigationStack {
            Group {
                if model.availableGroups.isEmpty {
                    emptyDirectory
                } else {
                    groupList
                }
            }
            .navigationTitle("Filtra per colles")
            .agendaInlineNavigationTitle()
            .agendaGroupSearch(text: $searchText)
            .agendaOpaqueNavigationBar(background: agendaGroupFilterBackground)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fet") { dismiss() }
                }
            }
        }
        .background(agendaGroupFilterBackground.ignoresSafeArea())
        .presentationBackground(agendaGroupFilterBackground)
    }

    private var groupList: some View {
        List {
            if searchText.isEmpty {
                Section {
                    bulkSelectionButton(
                        title: "Totes les colles",
                        isSelected: !model.isGroupFilterActive,
                        action: model.toggleFollowingAllGroups
                    )
                }
            }

            if searchText.isEmpty {
                if !model.featuredGroups.isEmpty {
                    Section("Colles destacades") {
                        bulkSelectionButton(
                            title: "Totes les destacades",
                            isSelected: model.areAllFeaturedGroupsFollowed,
                            action: model.toggleFollowingFeaturedGroups
                        )
                        groupRows(model.featuredGroups)
                    }
                }
                Section("Totes les colles") {
                    groupRows(model.availableGroups)
                }
            } else {
                Section("Resultats") {
                    if filteredGroups.isEmpty {
                        Text("No s'ha trobat cap colla")
                            .foregroundStyle(.secondary)
                    } else {
                        groupRows(filteredGroups)
                    }
                }
            }

            if model.groupDirectoryErrorMessage != nil {
                Section {
                    Button("Torna a carregar el directori") {
                        Task { await model.loadGroupDirectory(forceRefresh: true) }
                    }
                } footer: {
                    Text("No s'ha pogut actualitzar el directori. Es mostra l'última còpia disponible.")
                }
            }
        }
        .refreshable { await model.loadGroupDirectory(forceRefresh: true) }
        .contentMargins(.top, 8, for: .scrollContent)
        .scrollContentBackground(.hidden)
        .background(agendaGroupFilterBackground)
    }

    private func bulkSelectionButton(
        title: String,
        isSelected: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            Label(
                title,
                systemImage: isSelected ? "checkmark.square.fill" : "square"
            )
            .foregroundStyle(isSelected ? Color.accentColor : Color.primary)
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }

    private var emptyDirectory: some View {
        ContentUnavailableView {
            Label("Directori no disponible", systemImage: "person.3")
        } description: {
            Text("Les actuacions continuen visibles mentre se segueixen totes les colles.")
        } actions: {
            Button("Torna-ho a provar") {
                Task { await model.loadGroupDirectory(forceRefresh: true) }
            }
        }
    }

    @ViewBuilder
    private func groupRows(_ groups: [String]) -> some View {
        ForEach(groups, id: \.self) { group in
            HStack(spacing: 12) {
                Button {
                    model.setFollowing(!model.isFollowing(groupName: group), groupName: group)
                } label: {
                    HStack(spacing: 12) {
                        Image(
                            systemName: model.isFollowing(groupName: group)
                                ? "checkmark.square.fill"
                                : "square"
                        )
                        .foregroundStyle(
                            model.isFollowing(groupName: group)
                                ? Color.accentColor
                                : Color.secondary
                        )
                        Text(group)
                            .foregroundStyle(.primary)
                            .multilineTextAlignment(.leading)
                        Spacer(minLength: 0)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(group)
                .accessibilityValue(
                    model.isFollowing(groupName: group) ? "Seleccionada" : "No seleccionada"
                )
                .accessibilityAddTraits(
                    model.isFollowing(groupName: group) ? .isSelected : []
                )

                Button {
                    model.setFeatured(!model.isFeatured(groupName: group), groupName: group)
                } label: {
                    Image(systemName: model.isFeatured(groupName: group) ? "star.fill" : "star")
                        .foregroundStyle(
                            model.isFeatured(groupName: group) ? Color.yellow : Color.secondary
                        )
                        .frame(width: 36, height: 36)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(
                    model.isFeatured(groupName: group)
                        ? "Treu \(group) de colles destacades"
                        : "Destaca \(group)"
                )
            }
        }
    }

    private var filteredGroups: [String] {
        model.availableGroups.filter {
            $0.range(
                of: searchText,
                options: [.caseInsensitive, .diacriticInsensitive],
                locale: Locale(identifier: "ca_ES")
            ) != nil
        }
    }

}

private extension View {
    @ViewBuilder
    func agendaInlineNavigationTitle() -> some View {
#if os(iOS)
        navigationBarTitleDisplayMode(.inline)
#else
        self
#endif
    }

    @ViewBuilder
    func agendaGroupSearch(text: Binding<String>) -> some View {
#if os(iOS)
        searchable(
            text: text,
            placement: .navigationBarDrawer(displayMode: .always),
            prompt: "Cerca una colla"
        )
#else
        searchable(text: text, prompt: "Cerca una colla")
#endif
    }

    @ViewBuilder
    func agendaOpaqueNavigationBar(background: Color) -> some View {
#if os(iOS)
        toolbarBackground(background, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
#else
        self
#endif
    }
}
