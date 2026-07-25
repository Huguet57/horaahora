import CastellsDomain

public extension AgendaViewModel {
    var availableGroups: [String] { groupFilter.availableGroups }
    var featuredGroups: [String] { groupFilter.featuredGroups }
    var areAllFeaturedGroupsFollowed: Bool { groupFilter.areAllFeaturedGroupsFollowed }
    var isGroupFilterActive: Bool { groupFilter.isActive }
    var selectedGroupCount: Int { groupFilter.selectedGroupCount }

    func isFollowing(groupName: String) -> Bool {
        groupFilter.isFollowing(groupName)
    }

    func isFeatured(groupName: String) -> Bool {
        groupFilter.isFeatured(groupName)
    }

    func setFollowing(_ following: Bool, groupName: String) {
        let previousSelection = groupFilter.selection
        groupFilter.setFollowing(following, groupName: groupName)
        finishGroupSelectionChange(from: previousSelection)
    }

    func followAllGroups() {
        let previousSelection = groupFilter.selection
        groupFilter.followAll()
        finishGroupSelectionChange(from: previousSelection)
    }

    func toggleFollowingAllGroups() {
        let previousSelection = groupFilter.selection
        groupFilter.toggleFollowingAll()
        finishGroupSelectionChange(from: previousSelection)
    }

    func toggleFollowingFeaturedGroups() {
        let previousSelection = groupFilter.selection
        groupFilter.toggleFollowingFeatured()
        finishGroupSelectionChange(from: previousSelection)
    }

    func setFeatured(_ featured: Bool, groupName: String) {
        groupFilter.setFeatured(featured, groupName: groupName)
    }

    func loadGroupDirectory(forceRefresh: Bool = false) async {
        groupDirectoryErrorMessage = nil
        guard let groupDirectoryRepository else {
            mergeObservedGroups()
            return
        }
        do {
            let directory = try await groupDirectoryRepository.groupDirectory(
                forceRefresh: forceRefresh
            )
            groupFilter.mergeDirectory(
                groups: directory.groups,
                revision: directory.revision,
                observedGroups: eventWindow.participatingGroupNames
            )
        } catch {
            groupDirectoryErrorMessage = error.localizedDescription
        }
    }
}

extension AgendaViewModel {
    var groupSelection: AgendaGroupSelection { groupFilter.selection }

    private func finishGroupSelectionChange(from previousSelection: AgendaGroupSelection) {
        guard groupFilter.selection != previousSelection else { return }
        updateVisibleMonthEvents()
    }

    func mergeObservedGroups() {
        groupFilter.mergeObservedGroups(eventWindow.participatingGroupNames)
    }
}
