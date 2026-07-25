import Foundation
import CastellsDomain

public protocol GroupDirectoryRemoteService: Sendable {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory
}

public struct HTTPGroupDirectoryRemoteService: GroupDirectoryRemoteService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        let query = forceRefresh
            ? [URLQueryItem(name: "refresh", value: "true")]
            : []
        return try await client.get(path: "/v1/groups", queryItems: query)
    }
}
