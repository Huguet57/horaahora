import Foundation

@MainActor
struct AgendaGroupFilter {
    private let store: (any AgendaFilterStoring)?
    private(set) var selection: AgendaGroupSelection
    private(set) var featuredGroupKeys: Set<String>
    private(set) var availableGroups: [String]
    private(set) var directoryRevision: String?

    init(store: (any AgendaFilterStoring)?) {
        let persisted = store?.load() ?? AgendaFilterState()
        self.store = store
        self.selection = persisted.selection
        self.featuredGroupKeys = persisted.featuredGroupKeys
        self.availableGroups = AgendaGroupNameNormalizer.merged(
            preferred: persisted.cachedGroups,
            fallback: []
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

    var selectedGroupCount: Int {
        switch selection {
        case .all:
            availableGroups.count
        case let .custom(keys):
            keys.intersection(Set(availableGroups.map { key(for: $0) })).count
        }
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

    func matches(participatingGroups: [String]) -> Bool {
        switch selection {
        case .all:
            true
        case let .custom(keys):
            participatingGroups.contains { keys.contains(key(for: $0)) }
        }
    }

    mutating func setFollowing(_ following: Bool, groupName: String) {
        let groupKey = key(for: groupName)
        switch selection {
        case .all:
            guard !following else { return }
            var keys = Set(availableGroups.map { key(for: $0) })
            keys.remove(groupKey)
            selection = .custom(keys)
        case let .custom(currentKeys):
            var keys = currentKeys
            if following { keys.insert(groupKey) } else { keys.remove(groupKey) }
            selection = .custom(keys)
        }
        persist()
    }

    mutating func followAll() {
        guard isActive else { return }
        selection = .all
        persist()
    }

    mutating func toggleFollowingAll() {
        selection = isActive ? .all : .custom([])
        persist()
    }

    mutating func toggleFollowingFeatured() {
        let featuredKeys = Set(featuredGroups.map { key(for: $0) })
        guard !featuredKeys.isEmpty else { return }
        switch selection {
        case .all:
            selection = .custom(
                Set(availableGroups.map { key(for: $0) }).subtracting(featuredKeys)
            )
        case let .custom(currentKeys):
            selection = .custom(
                areAllFeaturedGroupsFollowed
                    ? currentKeys.subtracting(featuredKeys)
                    : currentKeys.union(featuredKeys)
            )
        }
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
        availableGroups = AgendaGroupNameNormalizer.merged(
            preferred: groups,
            fallback: availableGroups + observedGroups
        )
        if !revision.isEmpty { directoryRevision = revision }
        persist()
    }

    mutating func mergeObservedGroups(_ groups: [String]) {
        availableGroups = AgendaGroupNameNormalizer.merged(
            preferred: availableGroups,
            fallback: groups
        )
        persist()
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
