import Foundation
import XCTest
@testable import CastellsData
import CastellsDomain

@MainActor
final class RemoteGroupDirectoryRepositoryTests: XCTestCase {
    func testDelegatesRefreshPolicyToTheDedicatedRemoteService() async throws {
        let remoteService = GroupDirectoryRemoteServiceStub()
        let repository = RemoteGroupDirectoryRepository(remoteService: remoteService)

        let directory = try await repository.groupDirectory(forceRefresh: true)
        let requestedForceRefresh = await remoteService.requestedForceRefresh

        XCTAssertEqual(directory.groups, ["Colla A"])
        XCTAssertTrue(requestedForceRefresh)
    }
}

private actor GroupDirectoryRemoteServiceStub: GroupDirectoryRemoteService {
    private(set) var requestedForceRefresh = false

    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        requestedForceRefresh = forceRefresh
        return CastellerGroupDirectory(
            groups: ["Colla A"],
            revision: "test",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}
