import SwiftUI

struct AgendaGroupFilterView: View {
    let model: AgendaViewModel
    let onRequestExpansion: () -> Void
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
                    AgendaGroupBulkSelectionButton(
                        title: "Totes les colles",
                        isSelected: !model.isGroupFilterActive,
                        action: model.toggleFollowingAllGroups
                    )
                }

                featuredSection

                Section("Totes les colles") {
                    groupRows(model.availableGroups)
                }
            } else {
                searchResultsSection
            }

            directoryErrorSection
        }
        .refreshable { await model.loadGroupDirectory(forceRefresh: true) }
        .contentMargins(.top, 8, for: .scrollContent)
        .scrollContentBackground(.hidden)
        .background(agendaGroupFilterBackground)
        .simultaneousGesture(groupListExpansionGesture)
    }

    @ViewBuilder
    private var featuredSection: some View {
        if !model.featuredGroups.isEmpty {
            Section("Colles destacades") {
                AgendaGroupBulkSelectionButton(
                    title: "Totes les destacades",
                    isSelected: model.areAllFeaturedGroupsFollowed,
                    action: model.toggleFollowingFeaturedGroups
                )
                groupRows(model.featuredGroups)
            }
        }
    }

    private var searchResultsSection: some View {
        Section("Resultats") {
            if filteredGroups.isEmpty {
                Text("No s'ha trobat cap colla")
                    .foregroundStyle(.secondary)
            } else {
                groupRows(filteredGroups)
            }
        }
    }

    @ViewBuilder
    private var directoryErrorSection: some View {
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
            let isFollowing = model.isFollowing(groupName: group)
            let isFeatured = model.isFeatured(groupName: group)
            AgendaGroupFilterRow(
                groupName: group,
                isFollowing: isFollowing,
                isFeatured: isFeatured,
                onToggleFollowing: {
                    model.setFollowing(!isFollowing, groupName: group)
                },
                onToggleFeatured: {
                    model.setFeatured(!isFeatured, groupName: group)
                }
            )
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

    private var groupListExpansionGesture: some Gesture {
        DragGesture(minimumDistance: AgendaGroupFilterSheetInteraction.minimumDragDistance)
            .onChanged { value in
                guard AgendaGroupFilterSheetInteraction.requestsExpansion(
                    translation: value.translation
                ) else { return }

                onRequestExpansion()
            }
    }
}

enum AgendaGroupFilterSheetInteraction {
    static let minimumDragDistance: CGFloat = 8

    static func requestsExpansion(translation: CGSize) -> Bool {
        translation.height < 0 && abs(translation.height) > abs(translation.width)
    }
}
