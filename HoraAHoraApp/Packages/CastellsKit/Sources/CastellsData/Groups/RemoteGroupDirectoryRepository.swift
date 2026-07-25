import CastellsDomain

@MainActor
public final class RemoteGroupDirectoryRepository: GroupDirectoryRepository {
    private let remoteService: any GroupDirectoryRemoteService

    public init(remoteService: any GroupDirectoryRemoteService) {
        self.remoteService = remoteService
    }

    public func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        try await remoteService.groupDirectory(forceRefresh: forceRefresh)
    }
}
