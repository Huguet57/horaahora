import CastellsDomain

enum HourByHourItemMerger {
    enum Policy: Equatable {
        case replace
        case append
        case revalidate
    }

    struct Result {
        let items: [HourByHourItem]
        let containsNewItems: Bool
    }

    static func merge(
        _ incoming: [HourByHourItem],
        into existing: [HourByHourItem],
        policy: Policy
    ) -> Result {
        let existingIdentities = Set(existing.map(HourByHourItemIdentity.init))
        let containsNewItems = policy == .revalidate
            && !existing.isEmpty
            && incoming.contains { !existingIdentities.contains(HourByHourItemIdentity($0)) }

        let candidates: [HourByHourItem]
        switch policy {
        case .replace:
            candidates = incoming
        case .append:
            candidates = existing + incoming
        case .revalidate:
            candidates = incoming + existing
        }

        var seen = Set<HourByHourItemIdentity>()
        let items = candidates.filter { seen.insert(HourByHourItemIdentity($0)).inserted }
        return Result(items: items, containsNewItems: containsNewItems)
    }
}

private struct HourByHourItemIdentity: Hashable {
    let sourceID: String
    let externalID: String

    init(_ item: HourByHourItem) {
        sourceID = item.sourceID
        externalID = item.externalID
    }
}
