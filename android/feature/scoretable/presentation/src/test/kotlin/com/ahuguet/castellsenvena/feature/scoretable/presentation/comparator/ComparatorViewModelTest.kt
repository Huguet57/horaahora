package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class ComparatorViewModelTest {
    private val rules = ComparatorRules(ScoreTable.bundled())
    private val storage = InMemoryComparatorStorage()

    /** A model with nothing saved: one scenario with Vilafranca and the Colla Vella. */
    private fun makeModel() = ComparatorViewModel(rules, storage)

    private val ComparatorViewModel.current get() = state.value.current

    private fun ComparatorViewModel.scenario(id: String) = state.value.scenarios.first { it.id == id }

    @Test
    fun addingACollaOnlyChangesTheScenarioOnScreen() {
        val model = makeModel()
        val first = model.current
        model.duplicateCurrent()

        model.addColla(KnownColla("Colla Joves", "JOVES"))

        assertEquals(listOf("VERDS", "VELLA", "JOVES"), model.current.colles.map { it.shortName })
        assertEquals(listOf("VERDS", "VELLA"), model.scenario(first.id).colles.map { it.shortName })
    }

    @Test
    fun changingAndRemovingACollaOnlyChangesTheScenarioOnScreen() {
        val model = makeModel()
        val first = model.current
        model.duplicateCurrent()
        val vella = model.current.colles.last()

        model.replaceColla(vella.id, KnownColla("Colla Joves", "JOVES"))
        assertEquals(listOf("VERDS", "JOVES"), model.current.colles.map { it.shortName })

        model.removeColla(vella.id)
        assertEquals(listOf("VERDS"), model.current.colles.map { it.shortName })
        assertEquals(listOf("VERDS", "VELLA"), model.scenario(first.id).colles.map { it.shortName })
    }

    @Test
    fun aFavouriteGoesToTheEndOfTheFavouritesOnTopAndBackToTheTopOfTheRest() {
        val model = makeModel()
        val first = model.current
        model.duplicateCurrent()
        model.duplicateCurrent()
        val last = model.current

        model.toggleFavorite(last.id)
        assertEquals(listOf(last.id), model.state.value.favorites.map { it.id })
        assertEquals(last.id, model.state.value.scenarios.first().id)

        model.toggleFavorite(first.id)
        assertEquals(listOf(last.id, first.id), model.state.value.favorites.map { it.id })

        model.toggleFavorite(last.id)
        assertEquals(listOf(first.id), model.state.value.favorites.map { it.id })
        assertEquals(last.id, model.state.value.others.first().id)
    }

    @Test
    fun scenariosMoveWithinTheirSection() {
        val model = makeModel()
        model.duplicateCurrent()
        model.duplicateCurrent()
        val ids = model.state.value.scenarios.map { it.id }

        model.moveScenario(favorites = false, from = 2, to = 0)

        assertEquals(listOf(ids[2], ids[0], ids[1]), model.state.value.scenarios.map { it.id })
    }

    @Test
    fun aDuplicateIsNotAFavourite() {
        val model = makeModel()
        val first = model.current
        model.toggleFavorite(first.id)

        model.duplicateCurrent()

        assertEquals(listOf(first.id), model.state.value.favorites.map { it.id })
        assertEquals(listOf(model.current.id), model.state.value.others.map { it.id })
    }

    @Test
    fun scenariosSavedBeforeFavouritesAndNamesStillLoad() {
        storage.value = """
            {"scenarios":[{"id":"A","colles":[{"id":"V","name":"Els meus","shortName":"MEUS","rounds":[null,null,null,null,null],"penalties":0}]}],"currentId":"A"}
        """.trimIndent()

        val scenario = makeModel().current

        assertFalse(scenario.isFavorite)
        assertNull(scenario.name)
        assertEquals(listOf("MEUS"), scenario.colles.map { it.shortName })
    }

    @Test
    fun aScenarioCanBeNamedAndTheNameCleared() {
        val model = makeModel()

        model.rename(model.current.id, "  Si la Vella carrega  ")
        assertEquals("Si la Vella carrega", model.current.name)

        model.rename(model.current.id, " ")
        assertNull(model.current.name)
    }

    @Test
    fun aDuplicateHasNoName() {
        val model = makeModel()
        model.rename(model.current.id, "Pla A")

        model.duplicateCurrent()

        assertNull(model.current.name)
    }

    @Test
    fun savedCollesTakeTheCurrentShortNameOfTheirColla() {
        storage.value = """
            {"scenarios":[{"id":"A","colles":[
                {"id":"V","name":"Vilafranca","shortName":"VIL"},
                {"id":"M","name":"Els meus","shortName":"MEUS"}
            ]}],"currentId":"A"}
        """.trimIndent()

        assertEquals(listOf("VERDS", "MEUS"), makeModel().current.colles.map { it.shortName })
    }

    @Test
    fun everyChangeIsSavedAndLoadsBack() {
        val model = makeModel()
        val cell = ComparatorCell(model.current.colles.first().id, round = 1)
        model.set(c("4de9f"), cell)
        model.rename(model.current.id, "Pla A")

        val reloaded = ComparatorViewModel(rules, storage)

        assertEquals("Pla A", reloaded.current.name)
        assertEquals(c("4de9f"), reloaded.castell(cell))
    }

    @Test
    fun aDeletedScenarioComesBackWhereItWas() {
        val model = makeModel()
        model.duplicateCurrent()
        model.duplicateCurrent()
        val ids = model.state.value.scenarios.map { it.id }

        val deleted = assertNotNull(model.delete(ids[1]))
        assertEquals(listOf(ids[0], ids[2]), model.state.value.scenarios.map { it.id })

        model.restore(deleted)
        assertEquals(ids, model.state.value.scenarios.map { it.id })
    }

    @Test
    fun theOnlyScenarioCannotBeDeleted() {
        val model = makeModel()

        assertNull(model.delete(model.current.id))
        assertEquals(1, model.state.value.scenarios.size)
    }

    @Test
    fun clearingTheRoundsKeepsTheCollesAndCanBeUndone() {
        val model = makeModel()
        val cell = ComparatorCell(model.current.colles.first().id, round = 0)
        model.set(d("3de9f"), cell)
        model.changePenalties(cell.collaId, 1)

        val before = model.clearCurrent()
        assertNull(model.castell(cell))
        assertEquals(0, model.current.colles.first().penalties)
        assertEquals(listOf("VERDS", "VELLA"), model.current.colles.map { it.shortName })

        model.restore(before)
        assertEquals(d("3de9f"), model.castell(cell))
        assertEquals(1, model.current.colles.first().penalties)
    }

    @Test
    fun theCastellListOpensOnTheRivalsCastellAndThenOnTheCollasLastOne() {
        val model = makeModel()
        val (verds, vella) = model.current.colles
        model.set(d("4de9f"), ComparatorCell(vella.id, round = 1))
        model.set(d("3de10fm"), ComparatorCell(verds.id, round = 0))

        assertEquals("4de9f", model.anchor(ComparatorCell(verds.id, round = 1)))
        assertEquals("3de10fm", model.anchor(ComparatorCell(verds.id, round = 2)))
    }

    @Test
    fun aCollaCannotBeInTheScenarioTwice() {
        val model = makeModel()
        val vella = model.current.colles.last()

        model.addColla(KnownColla.custom(" vilafranca "))
        model.replaceColla(vella.id, KnownColla("Vilafranca", "VERDS"))
        assertEquals(listOf("VERDS", "VELLA"), model.current.colles.map { it.shortName })

        // A colla may keep its own name.
        model.replaceColla(vella.id, KnownColla("Colla Vella", "VELLA"))
        assertEquals(listOf("Vilafranca", "Colla Vella"), model.current.colles.map { it.name })
    }

    @Test
    fun aCustomCollaIsShortenedToItsLastWord() {
        assertEquals(KnownColla("Castellers de la Vila", "VILA"), KnownColla.custom(" Castellers de la Vila "))
        assertEquals("MINYO", KnownColla.custom("Minyons").shortName)
    }
}
