import Foundation
import CastellsDomain

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
