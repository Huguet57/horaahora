import Foundation
import XCTest
@testable import FeatureAgenda

@MainActor
final class AgendaGroupFilterViewModelTests: XCTestCase {
    func testDefaultSelectionShowsEveryEventAndMergesDirectoryWithObservedGroups() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                fixture.event(id: "a", groups: ["colla observada"]),
                fixture.event(id: "empty", groups: [])
            ],
            groups: ["Colla Oficial", "Colla Observada"]
        )
        let model = repository.makeModel()
        model.selectedDate = fixture.day

        await model.load()
        await model.loadGroupDirectory()

        XCTAssertEqual(model.events.map(\.id), ["a", "empty"])
        XCTAssertTrue(model.otherEvents.isEmpty)
        XCTAssertEqual(model.availableGroups, ["Colla Observada", "Colla Oficial"])
        XCTAssertFalse(model.isGroupFilterActive)
        XCTAssertTrue(model.isFollowing(groupName: "Una colla futura"))
    }

    func testLoadsTheDirectoryFromItsDedicatedRepository() async {
        let agendaRepository = GroupAgendaRepositoryStub(items: [], groups: ["Colla Agenda"])
        let directoryRepository = GroupDirectoryRepositoryStub(groups: ["Colla Directori"])
        let model = AgendaViewModel(
            repository: agendaRepository,
            groupDirectoryRepository: directoryRepository
        )

        await model.loadGroupDirectory()

        XCTAssertEqual(model.availableGroups, ["Colla Directori"])
    }

    func testMissingDirectoryRepositoryKeepsGroupsObservedInAgendaEvents() async {
        let agendaRepository = GroupAgendaRepositoryStub(
            items: [fixture.event(id: "observed", groups: ["Colla Observada"])],
            groups: []
        )
        let model = AgendaViewModel(repository: agendaRepository)
        model.selectedDate = fixture.day

        await model.load()
        await model.loadGroupDirectory()

        XCTAssertEqual(model.availableGroups, ["Colla Observada"])
        XCTAssertNil(model.groupDirectoryErrorMessage)
    }

    func testCustomSelectionSplitsMatchingAndOtherEvents() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                fixture.event(id: "a-and-b", groups: ["Colla A", "Colla B"]),
                fixture.event(id: "only-b", groups: ["Colla B"]),
                fixture.event(id: "empty", groups: [])
            ],
            groups: ["Colla A", "Colla B"]
        )
        let model = repository.makeModel()
        model.selectedDate = fixture.day
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
                fixture.event(id: "gracia", groups: ["Castellers de la Vila de Gràcia"]),
                fixture.event(id: "blanes", groups: ["Colla Castellera de l'Alt Maresme"])
            ],
            groups: ["Castellers de la Vila de Gràcia", "Colla Castellera de l'Alt Maresme"]
        )
        let model = repository.makeModel()
        model.selectedDate = fixture.day
        await model.load()
        await model.loadGroupDirectory()
        model.toggleFollowingAllGroups()

        model.setFollowing(true, groupName: "Castellers de la Vila de Gràcia")

        XCTAssertEqual(model.events.map(\.id), ["gracia"])
        XCTAssertEqual(model.otherEvents.map(\.id), ["blanes"])
    }

    func testSelectionSnapshotChangesOnlyWhenTheFilterSelectionChanges() async {
        let model = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B"]
        ).makeModel()
        await model.loadGroupDirectory()

        let initialSelection = model.groupSelection

        model.setFeatured(true, groupName: "Colla A")
        model.setFollowing(true, groupName: "Colla A")

        XCTAssertEqual(model.groupSelection, initialSelection)

        model.setFollowing(false, groupName: "Colla B")

        let customSelection = model.groupSelection
        XCTAssertNotEqual(customSelection, initialSelection)

        model.setFollowing(false, groupName: "Colla B")

        XCTAssertEqual(model.groupSelection, customSelection)

        model.setFollowing(true, groupName: "Colla B")

        XCTAssertNotEqual(model.groupSelection, customSelection)
    }

    func testNewGroupsStayUnselectedInCustomModeButFollowAllRestoresAutomaticSelection() async {
        let repository = GroupAgendaRepositoryStub(items: [], groups: ["Colla A", "Colla B"])
        let model = repository.makeModel()
        await model.loadGroupDirectory()

        model.setFollowing(false, groupName: "Colla B")
        repository.directoryGroups.append("Colla C")
        await model.loadGroupDirectory(forceRefresh: true)

        XCTAssertFalse(model.isFollowing(groupName: "Colla C"))
        model.followAllGroups()
        XCTAssertTrue(model.isFollowing(groupName: "Colla C"))
        XCTAssertFalse(model.isGroupFilterActive)
    }

    func testAvailableGroupKeysStayPrecomputedAcrossDirectoryAndObservedGroupMerges() async {
        let repository = GroupAgendaRepositoryStub(
            items: [
                fixture.event(id: "observed", groups: ["Castellers de la Vila de Gràcia"])
            ],
            groups: ["Colla A"]
        )
        let model = repository.makeModel()
        model.selectedDate = fixture.day

        await model.load()
        await model.loadGroupDirectory()

        XCTAssertEqual(
            model.groupFilter.availableGroupKeys,
            ["castellers de la vila de gracia", "colla a"]
        )
        XCTAssertEqual(model.selectedGroupCount, 2)

        model.setFollowing(false, groupName: "Colla A")
        XCTAssertEqual(model.selectedGroupCount, 1)

        repository.directoryGroups.append("Colla B")
        await model.loadGroupDirectory(forceRefresh: true)

        XCTAssertEqual(
            model.groupFilter.availableGroupKeys,
            ["castellers de la vila de gracia", "colla a", "colla b"]
        )
        XCTAssertEqual(model.selectedGroupCount, 1)
    }

    func testTogglingAllGroupsOffClearsSelectionAndTogglingAgainFollowsAll() async {
        let model = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B"]
        ).makeModel()
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

    func testTogglingFeaturedGroupsChangesSelectionWithoutRemovingStars() async {
        let model = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B", "Colla C"]
        ).makeModel()
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

    func testFeaturingKeepsTheGroupInTheCompleteList() async {
        let model = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B"]
        ).makeModel()
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
        let first = GroupAgendaRepositoryStub(
            items: [],
            groups: ["Colla A", "Colla B"]
        ).makeModel(filterStore: store)
        await first.loadGroupDirectory()
        first.setFollowing(false, groupName: "Colla A")
        first.setFeatured(true, groupName: "Colla B")

        let restored = GroupAgendaRepositoryStub(items: [], groups: [])
            .makeModel(filterStore: store)

        XCTAssertTrue(restored.isGroupFilterActive)
        XCTAssertFalse(restored.isFollowing(groupName: "Colla A"))
        XCTAssertTrue(restored.isFeatured(groupName: "Colla B"))
        XCTAssertEqual(restored.availableGroups, ["Colla A", "Colla B"])
    }

    private var fixture: AgendaGroupFilterTestFixture.Type {
        AgendaGroupFilterTestFixture.self
    }
}
