import Foundation

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
