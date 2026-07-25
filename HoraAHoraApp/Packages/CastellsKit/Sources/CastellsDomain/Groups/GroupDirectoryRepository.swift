import Foundation

@MainActor
public protocol GroupDirectoryRepository: AnyObject {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory
}

public extension GroupDirectoryRepository {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        CastellerGroupDirectory(
            groups: [],
            revision: "",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}
