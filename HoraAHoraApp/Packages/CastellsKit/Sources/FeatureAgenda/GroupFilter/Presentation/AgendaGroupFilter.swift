import Foundation

@MainActor
struct AgendaGroupFilter {
    private let store: (any AgendaFilterStoring)?
    private(set) var selection: AgendaGroupSelection
    private(set) var featuredGroupKeys: Set<String>
    private(set) var availableGroups: [String]
    private(set) var availableGroupKeys: Set<String>
    private(set) var selectedGroupCount: Int
    private(set) var directoryRevision: String?

    init(store: (any AgendaFilterStoring)?) {
        let persisted = store?.load() ?? AgendaFilterState()
        let availableGroups = AgendaGroupNameNormalizer.merged(
            preferred: persisted.cachedGroups,
            fallback: []
        )
        let availableGroupKeys = Set(availableGroups.map(AgendaGroupNameNormalizer.key))
        self.store = store
        self.selection = persisted.selection
        self.featuredGroupKeys = persisted.featuredGroupKeys
        self.availableGroups = availableGroups
        self.availableGroupKeys = availableGroupKeys
        self.selectedGroupCount = Self.selectedGroupCount(
            for: persisted.selection,
            availableGroupKeys: availableGroupKeys
        )
        self.directoryRevision = persisted.directoryRevision
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
            var keys = availableGroupKeys
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
                availableGroupKeys.subtracting(featuredKeys)
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
        replaceAvailableGroups(
            AgendaGroupNameNormalizer.merged(
                preferred: groups,
                fallback: availableGroups + observedGroups
            )
        )
        if !revision.isEmpty { directoryRevision = revision }
        persist()
    }

    mutating func mergeObservedGroups(_ groups: [String]) {
        replaceAvailableGroups(
            AgendaGroupNameNormalizer.merged(
                preferred: availableGroups,
                fallback: groups
            )
        )
        persist()
    }

    private mutating func replaceAvailableGroups(_ groups: [String]) {
        availableGroups = groups
        availableGroupKeys = Set(groups.map(AgendaGroupNameNormalizer.key))
        refreshSelectedGroupCount()
    }

    private mutating func refreshSelectedGroupCount() {
        selectedGroupCount = Self.selectedGroupCount(
            for: selection,
            availableGroupKeys: availableGroupKeys
        )
    }

    private static func selectedGroupCount(
        for selection: AgendaGroupSelection,
        availableGroupKeys: Set<String>
    ) -> Int {
        switch selection {
        case .all:
            availableGroupKeys.count
        case let .custom(keys):
            keys.intersection(availableGroupKeys).count
        }
    }

    private func key(for groupName: String) -> String {
        AgendaGroupNameNormalizer.key(for: groupName)
    }

    private func persist() {
        store?.save(
            AgendaFilterState(
                selection: selection,
                featuredGroupKeys: featuredGroupKeys,
                cachedGroups: availableGroups,
                directoryRevision: directoryRevision
            )
        )
    }
}
