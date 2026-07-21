import Foundation
import CastellsDomain

public protocol ChatRemoteService: Sendable {
    func send(request: ChatRequest) async throws -> ChatResponse
}

public struct HTTPChatRemoteService: ChatRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func send(request: ChatRequest) async throws -> ChatResponse {
        try await client.post(path: "/v1/chat", body: request)
    }
}

public protocol HourByHourRemoteService: Sendable {
    func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage
}

public struct HTTPHourByHourRemoteService: HourByHourRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func page(cursor: String?, limit: Int, forceRefresh: Bool) async throws -> HourByHourPage {
        var query = [URLQueryItem(name: "limit", value: String(limit))]
        if let cursor { query.append(URLQueryItem(name: "cursor", value: cursor)) }
        if forceRefresh { query.append(URLQueryItem(name: "refresh", value: "true")) }
        return try await client.get(path: "/v1/hour-by-hour", queryItems: query)
    }
}

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
}

func agendaDateString(_ date: Date) -> String {
    let formatter = DateFormatter()
    formatter.calendar = Calendar(identifier: .gregorian)
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(identifier: "Europe/Madrid")
    formatter.dateFormat = "yyyy-MM-dd"
    return formatter.string(from: date)
}
