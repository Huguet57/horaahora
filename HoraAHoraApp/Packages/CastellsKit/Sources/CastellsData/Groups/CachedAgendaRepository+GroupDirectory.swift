import CastellsDomain

public extension CachedAgendaRepository {
    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        try await remoteService.groupDirectory(forceRefresh: forceRefresh)
    }
}
