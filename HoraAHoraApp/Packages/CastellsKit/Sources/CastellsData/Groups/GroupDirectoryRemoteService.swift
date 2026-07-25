import Foundation
import CastellsDomain

public protocol GroupDirectoryRemoteService: Sendable {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory
}

public extension GroupDirectoryRemoteService {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        CastellerGroupDirectory(
            groups: [],
            revision: "",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}

public extension HTTPAgendaRemoteService {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        let query = forceRefresh
            ? [URLQueryItem(name: "refresh", value: "true")]
            : []
        return try await client.get(path: "/v1/groups", queryItems: query)
    }
}
