import Foundation
import CastellsDomain

public enum AgendaGroupSelection: Codable, Equatable, Sendable {
    case all
    case custom(Set<String>)
}

public struct AgendaFilterState: Codable, Equatable, Sendable {
    public var selection: AgendaGroupSelection
    public var featuredGroupKeys: Set<String>
    public var cachedGroups: [String]
    public var directoryRevision: String?

    public init(
        selection: AgendaGroupSelection = .all,
        featuredGroupKeys: Set<String> = [],
        cachedGroups: [String] = [],
        directoryRevision: String? = nil
    ) {
        self.selection = selection
        self.featuredGroupKeys = featuredGroupKeys
        self.cachedGroups = cachedGroups
        self.directoryRevision = directoryRevision
    }
}

@MainActor
public protocol AgendaFilterStoring: AnyObject {
    func load() -> AgendaFilterState
    func save(_ state: AgendaFilterState)
}

@MainActor
public final class AgendaUserDefaultsStore: AgendaFilterStoring {
    public static let defaultKey = "castells.agenda.group-filter.v1"

    private let userDefaults: UserDefaults
    private let key: String

    public init(
        userDefaults: UserDefaults = .standard,
        key: String = AgendaUserDefaultsStore.defaultKey
    ) {
        self.userDefaults = userDefaults
        self.key = key
    }

    public func load() -> AgendaFilterState {
        guard
            let data = userDefaults.data(forKey: key),
            let state = try? JSONDecoder().decode(AgendaFilterState.self, from: data)
        else {
            return AgendaFilterState()
        }
        return state
    }

    public func save(_ state: AgendaFilterState) {
        guard let data = try? JSONEncoder().encode(state) else { return }
        userDefaults.set(data, forKey: key)
    }
}

func agendaGroupKey(_ name: String) -> String {
    let apostropheNormalized = name
        .replacingOccurrences(of: "’", with: "'")
        .replacingOccurrences(of: "‘", with: "'")
        .replacingOccurrences(of: "ʼ", with: "'")
    let folded = apostropheNormalized.folding(
        options: [.caseInsensitive, .diacriticInsensitive, .widthInsensitive],
        locale: Locale(identifier: "ca_ES")
    )
    return folded.split(whereSeparator: \.isWhitespace).joined(separator: " ")
}

func agendaSortedGroupNames(_ names: [String]) -> [String] {
    names.sorted {
        $0.compare(
            $1,
            options: [.caseInsensitive, .diacriticInsensitive],
            range: nil,
            locale: Locale(identifier: "ca_ES")
        ) == .orderedAscending
    }
}

func agendaMergedGroupNames(preferred: [String], fallback: [String]) -> [String] {
    var byKey: [String: String] = [:]
    for name in preferred + fallback {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { continue }
        let key = agendaGroupKey(trimmed)
        if byKey[key] == nil {
            byKey[key] = trimmed
        }
    }
    return agendaSortedGroupNames(Array(byKey.values))
}
