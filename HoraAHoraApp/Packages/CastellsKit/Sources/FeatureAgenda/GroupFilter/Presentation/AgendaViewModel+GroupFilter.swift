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
        groupFilter.setFollowing(following, groupName: groupName)
        updateVisibleMonthEvents()
    }

    func followAllGroups() {
        groupFilter.followAll()
        updateVisibleMonthEvents()
    }

    func toggleFollowingAllGroups() {
        groupFilter.toggleFollowingAll()
        updateVisibleMonthEvents()
    }

    func toggleFollowingFeaturedGroups() {
        groupFilter.toggleFollowingFeatured()
        updateVisibleMonthEvents()
    }

    func setFeatured(_ featured: Bool, groupName: String) {
        groupFilter.setFeatured(featured, groupName: groupName)
    }

    func loadGroupDirectory(forceRefresh: Bool = false) async {
        groupDirectoryErrorMessage = nil
        do {
            let directory = try await repository.groupDirectory(forceRefresh: forceRefresh)
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
    func mergeObservedGroups() {
        groupFilter.mergeObservedGroups(eventWindow.participatingGroupNames)
    }
}
