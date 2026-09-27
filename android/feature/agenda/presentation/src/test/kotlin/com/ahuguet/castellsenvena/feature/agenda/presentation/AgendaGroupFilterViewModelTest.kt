package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaGroupFilterFixture.event
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.coroutines.test.runTest

class AgendaGroupFilterViewModelTest {
    @Test
    fun defaultSelectionShowsEveryEventAndMergesDirectoryWithObservedGroups() = runTest {
        val repository = GroupAgendaRepositoryStub(
            suppliedItems = listOf(event("a", listOf("colla observada")), event("empty", emptyList())),
            directoryGroups = listOf("Colla Oficial", "Colla Observada"),
        )
        val model = repository.makeModel()
        model.selectedDate = AgendaGroupFilterFixture.day

        model.load()
        model.loadGroupDirectory()

        val state = model.state.value
        assertEquals(listOf("a", "empty"), state.events.map { it.id })
        assertTrue(state.otherEvents.isEmpty())
        assertEquals(listOf("Colla Observada", "Colla Oficial"), state.groupFilter.availableGroups)
        assertFalse(state.groupFilter.isActive)
        assertTrue(model.isFollowing("Una colla futura"))
        assertTrue(state.groupFilter.isFollowing("Una colla futura"))
    }

    @Test
    fun loadsTheDirectoryFromItsDedicatedRepository() = runTest {
        val model = AgendaViewModel(
            repository = GroupAgendaRepositoryStub(emptyList(), listOf("Colla Agenda")),
            groupDirectoryRepository = GroupDirectoryRepositoryStub(listOf("Colla Directori")),
        )

        model.loadGroupDirectory()

        assertEquals(listOf("Colla Directori"), model.state.value.groupFilter.availableGroups)
    }

    @Test
    fun missingDirectoryRepositoryKeepsGroupsObservedInAgendaEvents() = runTest {
        val model = AgendaViewModel(
            repository = GroupAgendaRepositoryStub(listOf(event("observed", listOf("Colla Observada"))), emptyList()),
        )
        model.selectedDate = AgendaGroupFilterFixture.day

        model.load()
        model.loadGroupDirectory()

        assertEquals(listOf("Colla Observada"), model.state.value.groupFilter.availableGroups)
        assertNull(model.state.value.groupDirectoryErrorMessage)
    }

    @Test
    fun customSelectionSplitsMatchingAndOtherEvents() = runTest {
        val repository = GroupAgendaRepositoryStub(
            suppliedItems = listOf(
                event("a-and-b", listOf("Colla A", "Colla B")),
                event("only-b", listOf("Colla B")),
                event("empty", emptyList()),
            ),
            directoryGroups = listOf("Colla A", "Colla B"),
        )
        val model = repository.makeModel()
        model.selectedDate = AgendaGroupFilterFixture.day
        model.load()
        model.loadGroupDirectory()

        model.setFollowing(false, "Colla B")

        val state = model.state.value
        assertEquals(listOf("a-and-b"), state.events.map { it.id })
        assertEquals(listOf("only-b", "empty"), state.otherEvents.map { it.id })
        assertEquals(setOf("2026-07-25"), state.eventDateKeys)
        assertEquals(1, state.groupFilter.selectedGroupCount)
        assertEquals(2, repository.eventRequestCount)
    }

    @Test
    fun selectingGraciaMovesItsEventOutOfOtherEvents() = runTest {
        val repository = GroupAgendaRepositoryStub(
            suppliedItems = listOf(
                event("gracia", listOf("Castellers de la Vila de Gràcia")),
                event("blanes", listOf("Colla Castellera de l'Alt Maresme")),
            ),
            directoryGroups = listOf("Castellers de la Vila de Gràcia", "Colla Castellera de l'Alt Maresme"),
        )
        val model = repository.makeModel()
        model.selectedDate = AgendaGroupFilterFixture.day
        model.load()
        model.loadGroupDirectory()
        model.toggleFollowingAllGroups()

        model.setFollowing(true, "Castellers de la Vila de Gràcia")

        assertEquals(listOf("gracia"), model.state.value.events.map { it.id })
        assertEquals(listOf("blanes"), model.state.value.otherEvents.map { it.id })
    }

    @Test
    fun selectionSnapshotChangesOnlyWhenTheFilterSelectionChanges() = runTest {
        val model = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B")).makeModel()
        model.loadGroupDirectory()
        val initialSelection = model.groupSelection

        model.setFeatured(true, "Colla A")
        model.setFollowing(true, "Colla A")
        assertEquals(initialSelection, model.groupSelection)

        model.setFollowing(false, "Colla B")
        val customSelection = model.groupSelection
        assertNotEquals(initialSelection, customSelection)

        model.setFollowing(false, "Colla B")
        assertEquals(customSelection, model.groupSelection)

        model.setFollowing(true, "Colla B")
        assertNotEquals(customSelection, model.groupSelection)
    }

    @Test
    fun newGroupsStayUnselectedInCustomModeButFollowAllRestoresAutomaticSelection() = runTest {
        val repository = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B"))
        val model = repository.makeModel()
        model.loadGroupDirectory()

        model.setFollowing(false, "Colla B")
        repository.directoryGroups = repository.directoryGroups + "Colla C"
        model.loadGroupDirectory(forceRefresh = true)

        assertFalse(model.isFollowing("Colla C"))
        model.followAllGroups()
        assertTrue(model.isFollowing("Colla C"))
        assertFalse(model.state.value.groupFilter.isActive)
    }

    @Test
    fun selectedGroupCountStaysInSyncAcrossDirectoryAndObservedGroupMerges() = runTest {
        val repository = GroupAgendaRepositoryStub(
            suppliedItems = listOf(event("observed", listOf("Castellers de la Vila de Gràcia"))),
            directoryGroups = listOf("Colla A"),
        )
        val model = repository.makeModel()
        model.selectedDate = AgendaGroupFilterFixture.day

        model.load()
        model.loadGroupDirectory()
        assertEquals(2, model.state.value.groupFilter.selectedGroupCount)

        model.setFollowing(false, "Colla A")
        assertEquals(1, model.state.value.groupFilter.selectedGroupCount)

        repository.directoryGroups = repository.directoryGroups + "Colla B"
        model.loadGroupDirectory(forceRefresh = true)
        assertEquals(1, model.state.value.groupFilter.selectedGroupCount)
    }

    @Test
    fun togglingAllGroupsOffClearsSelectionAndTogglingAgainFollowsAll() = runTest {
        val model = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B")).makeModel()
        model.loadGroupDirectory()

        model.toggleFollowingAllGroups()

        assertTrue(model.state.value.groupFilter.isActive)
        assertEquals(0, model.state.value.groupFilter.selectedGroupCount)
        assertFalse(model.isFollowing("Colla A"))
        assertFalse(model.isFollowing("Colla B"))

        model.toggleFollowingAllGroups()

        assertFalse(model.state.value.groupFilter.isActive)
        assertEquals(2, model.state.value.groupFilter.selectedGroupCount)
        assertTrue(model.isFollowing("Una colla futura"))
    }

    @Test
    fun togglingFeaturedGroupsChangesSelectionWithoutRemovingStars() = runTest {
        val model = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B", "Colla C")).makeModel()
        model.loadGroupDirectory()
        model.setFeatured(true, "Colla A")
        model.setFeatured(true, "Colla B")
        assertTrue(model.state.value.groupFilter.areAllFeaturedGroupsFollowed)

        model.toggleFollowingFeaturedGroups()

        assertFalse(model.state.value.groupFilter.areAllFeaturedGroupsFollowed)
        assertFalse(model.isFollowing("Colla A"))
        assertFalse(model.isFollowing("Colla B"))
        assertTrue(model.isFollowing("Colla C"))
        assertEquals(listOf("Colla A", "Colla B"), model.state.value.groupFilter.featuredGroups)

        model.toggleFollowingFeaturedGroups()

        assertTrue(model.state.value.groupFilter.areAllFeaturedGroupsFollowed)
        assertTrue(model.isFollowing("Colla A"))
        assertTrue(model.isFollowing("Colla B"))
        assertEquals(listOf("Colla A", "Colla B"), model.state.value.groupFilter.featuredGroups)
    }

    @Test
    fun featuringKeepsTheGroupInTheCompleteList() = runTest {
        val model = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B")).makeModel()
        model.loadGroupDirectory()

        model.setFeatured(true, "Colla B")

        assertTrue(model.isFollowing("Colla B"))
        assertTrue(model.state.value.groupFilter.isFeatured("Colla B"))
        assertEquals(listOf("Colla B"), model.state.value.groupFilter.featuredGroups)
        assertEquals(listOf("Colla A", "Colla B"), model.state.value.groupFilter.availableGroups)
    }

    @Test
    fun filterFeaturedGroupsAndDirectorySurviveModelRecreation() = runTest {
        val store = InMemoryAgendaFilterStore()
        val first = GroupAgendaRepositoryStub(emptyList(), listOf("Colla A", "Colla B")).makeModel(store)
        first.loadGroupDirectory()
        first.setFollowing(false, "Colla A")
        first.setFeatured(true, "Colla B")

        val restored = GroupAgendaRepositoryStub(emptyList(), emptyList()).makeModel(store)

        assertTrue(restored.state.value.groupFilter.isActive)
        assertFalse(restored.isFollowing("Colla A"))
        assertTrue(restored.isFeatured("Colla B"))
        assertEquals(listOf("Colla A", "Colla B"), restored.state.value.groupFilter.availableGroups)
    }
}
