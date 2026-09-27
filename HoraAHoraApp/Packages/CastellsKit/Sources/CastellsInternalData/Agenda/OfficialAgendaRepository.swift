import Foundation
import CastellsDomain

@MainActor
public final class OfficialAgendaRepository: AgendaRepository {
    public let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!

    public init() {}

    public func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage {
        AgendaPage(
            items: [],
            nextCursor: nil,
            officialURL: officialURL,
            fromCache: true,
            sourceStatus: .unavailable
        )
    }
}
