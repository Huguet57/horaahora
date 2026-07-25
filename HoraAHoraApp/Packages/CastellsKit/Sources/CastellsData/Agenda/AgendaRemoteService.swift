import Foundation
import CastellsDomain

public protocol AgendaRemoteService: Sendable {
    func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory
}

public extension AgendaRemoteService {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        CastellerGroupDirectory(
            groups: [],
            revision: "",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}

public struct HTTPAgendaRemoteService: AgendaRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage {
        var query = [
            URLQueryItem(name: "from", value: agendaDateString(from)),
            URLQueryItem(name: "to", value: agendaDateString(to)),
            URLQueryItem(name: "limit", value: String(limit)),
        ]
        if let group, !group.isEmpty {
            query.append(URLQueryItem(name: "group", value: group))
        }
        if let municipality, !municipality.isEmpty {
            query.append(URLQueryItem(name: "municipality", value: municipality))
        }
        if let cursor { query.append(URLQueryItem(name: "cursor", value: cursor)) }
        if forceRefresh { query.append(URLQueryItem(name: "refresh", value: "true")) }
        return try await client.get(path: "/v1/events", queryItems: query)
    }

    public func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        var query: [URLQueryItem] = []
        if forceRefresh {
            query.append(URLQueryItem(name: "refresh", value: "true"))
        }
        return try await client.get(path: "/v1/groups", queryItems: query)
    }
}

func agendaDateString(_ date: Date) -> String {
    let formatter = DateFormatter()
    formatter.calendar = Calendar(identifier: .gregorian)
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(identifier: "Europe/Madrid")
    formatter.dateFormat = "yyyy-MM-dd"
    return formatter.string(from: date)
}
