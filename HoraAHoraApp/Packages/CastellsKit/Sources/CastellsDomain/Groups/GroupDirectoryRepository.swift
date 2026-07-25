@MainActor
public protocol GroupDirectoryRepository: AnyObject {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory
}
