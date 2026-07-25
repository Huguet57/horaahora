import Foundation
import CastellsDomain
@testable import FeatureAgenda

@MainActor
enum AgendaGroupFilterTestFixture {
    static var day: Date {
        var components = DateComponents()
        components.calendar = AgendaCalendarMath.calendar
        components.timeZone = AgendaCalendarMath.calendar.timeZone
        components.year = 2026
        components.month = 7
        components.day = 25
        return components.date!
    }

    static func event(id: String, groups: [String]) -> CastellEvent {
        CastellEvent(
            id: id,
            sourceID: "cccc",
            externalID: id,
            title: id,
            localDate: "2026-07-25",
            startsAt: nil,
            timeLabel: "Tarda",
            timezone: "Europe/Madrid",
            venue: "Plaça",
            municipality: "Valls",
            participatingGroups: groups,
            notes: "",
            sourceURL: URL(string: "https://castellscat.cat/ca/agenda")!,
            sourceOrder: 0,
            attribution: "Font: CCCC",
            revision: "r1",
            updatedAt: Date()
        )
    }
}

@MainActor
final class GroupAgendaRepositoryStub: AgendaRepository {
    let officialURL = URL(string: "https://castellscat.cat/ca/agenda")!
    let suppliedItems: [CastellEvent]
    var directoryGroups: [String]
    private(set) var eventRequestCount = 0

    init(items: [CastellEvent], groups: [String]) {
        suppliedItems = items
        directoryGroups = groups
    }

    func events(
        from: Date,
        to: Date,
        group: String?,
        municipality: String?,
        cursor: String?,
        limit: Int,
        forceRefresh: Bool
    ) async throws -> AgendaPage {
        eventRequestCount += 1
        return AgendaPage(
            items: suppliedItems,
            nextCursor: nil,
            officialURL: officialURL,
            fromCache: false,
            sourceStatus: .active
        )
    }

    func groupDirectory(forceRefresh: Bool) async throws -> CastellerGroupDirectory {
        CastellerGroupDirectory(
            groups: directoryGroups,
            revision: "test",
            officialURL: URL(string: "https://castellscat.cat/public/ca/les-colles-llistat")!
        )
    }
}
