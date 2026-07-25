struct AgendaGroupCatalog {
    private(set) var names: [String]
    private(set) var keys: Set<String>

    init(preferred: [String], fallback: [String] = []) {
        let names = AgendaGroupNameNormalizer.merged(
            preferred: preferred,
            fallback: fallback
        )
        self.names = names
        self.keys = Set(names.map(AgendaGroupNameNormalizer.key))
    }

    mutating func replace(preferred: [String], fallback: [String]) {
        self = AgendaGroupCatalog(preferred: preferred, fallback: fallback)
    }

    func selectedCount(for selection: AgendaGroupSelection) -> Int {
        switch selection {
        case .all:
            keys.count
        case let .custom(selectedKeys):
            selectedKeys.intersection(keys).count
        }
    }
}
