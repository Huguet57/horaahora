import Foundation
import XCTest
import CastellsDomain
@testable import FeatureAgenda

@MainActor
final class AgendaGroupFilterTests: XCTestCase {
    func testGroupKeysIgnoreCaseAccentsWhitespaceAndApostropheVariants() {
        XCTAssertEqual(
            agendaGroupKey("  Castellers   d’Àltafulla "),
            agendaGroupKey("castellers d'altafulla")
        )
    }

    func testDefaultSelectionShowsEveryEventAndMergesDirectoryWithObservedGroups() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                event(id: "a", groups: ["colla observada"]),
                event(id: "empty", groups: [])
            ],
            groups: ["Colla Oficial", "Colla Observada"]
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = day

        await model.load()
        await model.loadGroupDirectory()

        XCTAssertEqual(model.events.map(\.id), ["a", "empty"])
        XCTAssertTrue(model.otherEvents.isEmpty)
        XCTAssertEqual(model.availableGroups, ["Colla Observada", "Colla Oficial"])
        XCTAssertFalse(model.isGroupFilterActive)
        XCTAssertTrue(model.isFollowing(groupName: "Una colla futura"))
    }

    func testCustomSelectionSplitsMatchingAndOtherEvents() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                event(id: "a-and-b", groups: ["Colla A", "Colla B"]),
                event(id: "only-b", groups: ["Colla B"]),
                event(id: "empty", groups: [])
            ],
            groups: ["Colla A", "Colla B"]
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = day
        await model.load()
        await model.loadGroupDirectory()

        model.setFollowing(false, groupName: "Colla B")

        XCTAssertEqual(model.events.map(\.id), ["a-and-b"])
        XCTAssertEqual(model.otherEvents.map(\.id), ["only-b", "empty"])
        XCTAssertEqual(model.eventDateKeys, ["2026-07-25"])
        XCTAssertEqual(model.selectedGroupCount, 1)
        XCTAssertEqual(repository.eventRequestCount, 2)
    }

    func testSelectingGraciaMovesItsEventOutOfOtherEvents() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                event(id: "gracia", groups: ["Castellers de la Vila de Gràcia"]),
                event(id: "blanes", groups: ["Colla Castellera de l'Alt Maresme"])
            ],
            groups: ["Castellers de la Vila de Gràcia", "Colla Castellera de l'Alt Maresme"]
        )
        let model = AgendaViewModel(repository: repository)
        model.selectedDate = day
        await model.load()
        await model.loadGroupDirectory()
        model.toggleFollowingAllGroups()

        model.setFollowing(true, groupName: "Castellers de la Vila de Gràcia")

        XCTAssertEqual(model.events.map(\.id), ["gracia"])
        XCTAssertEqual(model.otherEvents.map(\.id), ["blanes"])
    }

    func testNewGroupsStayUnselectedInCustomModeButFollowAllRestoresAutomaticSelection() async {
        let repository = GroupAgendaRepositoryStub(items: [], groups: ["Colla A", "Colla B"])
        let model = AgendaViewModel(repository: repository)
        await model.loadGroupDirectory()

        model.setFollowing(false, groupName: "Colla B")
        repository.directoryGroups.append("Colla C")
        await model.loadGroupDirectory(forceRefresh: true)

        XCTAssertFalse(model.isFollowing(groupName: "Colla C"))
        model.followAllGroups()
        XCTAssertTrue(model.isFollowing(groupName: "Colla C"))
        XCTAssertFalse(model.isGroupFilterActive)
    }

    func testTogglingAllGroupsOffClearsTheSelectionAndTogglingAgainFollowsAll() async {
        let repository = GroupAgendaRepositoryStub(items: [], groups: ["Colla A", "Colla B"])
        let model = AgendaViewModel(repository: repository)
        await model.loadGroupDirectory()

        model.toggleFollowingAllGroups()

        XCTAssertTrue(model.isGroupFilterActive)
        XCTAssertEqual(model.selectedGroupCount, 0)
        XCTAssertFalse(model.isFollowing(groupName: "Colla A"))
        XCTAssertFalse(model.isFollowing(groupName: "Colla B"))

        model.toggleFollowingAllGroups()

        XCTAssertFalse(model.isGroupFilterActive)
        XCTAssertEqual(model.selectedGroupCount, 2)
        XCTAssertTrue(model.isFollowing(groupName: "Una colla futura"))
    }

    func testTogglingFeaturedGroupsChangesTheirSelectionWithoutRemovingStars() async {
        let repository = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B", "Colla C"]
        )
        let model = AgendaViewModel(repository: repository)
        await model.loadGroupDirectory()
        model.setFeatured(true, groupName: "Colla A")
        model.setFeatured(true, groupName: "Colla B")

        XCTAssertTrue(model.areAllFeaturedGroupsFollowed)

        model.toggleFollowingFeaturedGroups()

        XCTAssertFalse(model.areAllFeaturedGroupsFollowed)
        XCTAssertFalse(model.isFollowing(groupName: "Colla A"))
        XCTAssertFalse(model.isFollowing(groupName: "Colla B"))
        XCTAssertTrue(model.isFollowing(groupName: "Colla C"))
        XCTAssertEqual(model.featuredGroups, ["Colla A", "Colla B"])

        model.toggleFollowingFeaturedGroups()

        XCTAssertTrue(model.areAllFeaturedGroupsFollowed)
        XCTAssertTrue(model.isFollowing(groupName: "Colla A"))
        XCTAssertTrue(model.isFollowing(groupName: "Colla B"))
        XCTAssertEqual(model.featuredGroups, ["Colla A", "Colla B"])
    }

    func testFeaturingAddsTheGroupToHighlightedWithoutRemovingItFromAllGroups() async {
        let repository = GroupAgendaRepositoryStub(items: [], groups: ["Colla A", "Colla B"])
        let model = AgendaViewModel(repository: repository)
        await model.loadGroupDirectory()

        model.setFeatured(true, groupName: "Colla B")

        XCTAssertTrue(model.isFollowing(groupName: "Colla B"))
        XCTAssertEqual(model.featuredGroups, ["Colla B"])
        XCTAssertEqual(model.availableGroups, ["Colla A", "Colla B"])
    }

    func testFilterFeaturedGroupsAndDirectorySurviveModelRecreation() async throws {
        let suiteName = "AgendaGroupFilterTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let store = AgendaUserDefaultsStore(userDefaults: defaults, key: "agenda-test")
        let repository = GroupAgendaRepositoryStub(items: [], groups: ["Colla A", "Colla B"])
        let first = AgendaViewModel(repository: repository, filterStore: store)
        await first.loadGroupDirectory()
        first.setFollowing(false, groupName: "Colla A")
        first.setFeatured(true, groupName: "Colla B")

        let restored = AgendaViewModel(
            repository: GroupAgendaRepositoryStub(items: [], groups: []),
            filterStore: store
        )

        XCTAssertTrue(restored.isGroupFilterActive)
        XCTAssertFalse(restored.isFollowing(groupName: "Colla A"))
        XCTAssertTrue(restored.isFeatured(groupName: "Colla B"))
        XCTAssertEqual(restored.availableGroups, ["Colla A", "Colla B"])
    }

    private var day: Date {
        var components = DateComponents()
        components.calendar = AgendaCalendarMath.calendar
        components.timeZone = AgendaCalendarMath.calendar.timeZone
        components.year = 2026
        components.month = 7
        components.day = 25
        return components.date!
    }

    private func event(id: String, groups: [String]) -> CastellEvent {
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
private final class GroupAgendaRepositoryStub: AgendaRepository {
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
