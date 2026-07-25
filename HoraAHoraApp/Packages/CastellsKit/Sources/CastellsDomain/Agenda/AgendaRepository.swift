import Foundation

@MainActor
public protocol AgendaRepository: AnyObject {
    var officialURL: URL { get }
    func cachedEvents(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?
    ) throws -> [CastellEvent]
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

public extension AgendaRepository {
    func cachedEvents(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?
    ) throws -> [CastellEvent] {
        []
    }

    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        CastellerGroupDirectory(
            groups: [],
            revision: "",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}
