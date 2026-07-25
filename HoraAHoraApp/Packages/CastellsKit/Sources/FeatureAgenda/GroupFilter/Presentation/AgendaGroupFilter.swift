import Foundation

@MainActor
struct AgendaGroupFilter {
    private let store: (any AgendaFilterStoring)?
    private(set) var selection: AgendaGroupSelection
    private(set) var featuredGroupKeys: Set<String>
    private var catalog: AgendaGroupCatalog
    private(set) var selectedGroupCount: Int
    private(set) var directoryRevision: String?

    init(store: (any AgendaFilterStoring)?) {
        let persisted = store?.load() ?? AgendaFilterState()
        let catalog = AgendaGroupCatalog(preferred: persisted.cachedGroups)
        self.store = store
        self.selection = persisted.selection
        self.featuredGroupKeys = persisted.featuredGroupKeys
        self.catalog = catalog
        self.selectedGroupCount = catalog.selectedCount(for: persisted.selection)
        self.directoryRevision = persisted.directoryRevision
    }

    var availableGroups: [String] {
        catalog.names
    }

    var featuredGroups: [String] {
        availableGroups.filter { featuredGroupKeys.contains(key(for: $0)) }
    }

    var areAllFeaturedGroupsFollowed: Bool {
        !featuredGroups.isEmpty && featuredGroups.allSatisfy(isFollowing)
    }

    var isActive: Bool {
        if case .custom = selection { return true }
        return false
    }

    func isFollowing(_ groupName: String) -> Bool {
        switch selection {
        case .all:
            true
        case let .custom(keys):
            keys.contains(key(for: groupName))
        }
    }

    func isFeatured(_ groupName: String) -> Bool {
        featuredGroupKeys.contains(key(for: groupName))
    }

    func matches(participatingGroupKeys: Set<String>) -> Bool {
        switch selection {
        case .all:
            true
        case let .custom(keys):
            !keys.isDisjoint(with: participatingGroupKeys)
        }
    }

    mutating func setFollowing(_ following: Bool, groupName: String) {
        let groupKey = key(for: groupName)
        switch selection {
        case .all:
            guard !following else { return }
            var keys = catalog.keys
            keys.remove(groupKey)
            selection = .custom(keys)
        case let .custom(currentKeys):
            var keys = currentKeys
            if following { keys.insert(groupKey) } else { keys.remove(groupKey) }
            selection = .custom(keys)
        }
        refreshSelectedGroupCount()
        persist()
    }

    mutating func followAll() {
        guard isActive else { return }
        selection = .all
        refreshSelectedGroupCount()
        persist()
    }

    mutating func toggleFollowingAll() {
        selection = isActive ? .all : .custom([])
        refreshSelectedGroupCount()
        persist()
    }

    mutating func toggleFollowingFeatured() {
        let featuredKeys = Set(featuredGroups.map { key(for: $0) })
        guard !featuredKeys.isEmpty else { return }
        switch selection {
        case .all:
            selection = .custom(
                catalog.keys.subtracting(featuredKeys)
            )
        case let .custom(currentKeys):
            selection = .custom(
                areAllFeaturedGroupsFollowed
                    ? currentKeys.subtracting(featuredKeys)
                    : currentKeys.union(featuredKeys)
            )
        }
        refreshSelectedGroupCount()
        persist()
    }

    mutating func setFeatured(_ featured: Bool, groupName: String) {
        let groupKey = key(for: groupName)
        if featured { featuredGroupKeys.insert(groupKey) } else { featuredGroupKeys.remove(groupKey) }
        persist()
    }

    mutating func mergeDirectory(
        groups: [String],
        revision: String,
        observedGroups: [String]
    ) {
        catalog.replace(
            preferred: groups,
            fallback: catalog.names + observedGroups
        )
        refreshSelectedGroupCount()
        if !revision.isEmpty { directoryRevision = revision }
        persist()
    }

    mutating func mergeObservedGroups(_ groups: [String]) {
        catalog.replace(
            preferred: catalog.names,
            fallback: groups
        )
        refreshSelectedGroupCount()
        persist()
    }

    private mutating func refreshSelectedGroupCount() {
        selectedGroupCount = catalog.selectedCount(for: selection)
    }

    private func key(for groupName: String) -> String {
        AgendaGroupNameNormalizer.key(for: groupName)
    }

    private func persist() {
        store?.save(
            AgendaFilterState(
                selection: selection,
                featuredGroupKeys: featuredGroupKeys,
                cachedGroups: catalog.names,
                directoryRevision: directoryRevision
            )
        )
    }
}
