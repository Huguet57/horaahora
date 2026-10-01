package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ComparatorViewModelTest {
    private val rules = ComparatorRules(ScoreTable.bundled())
    private val storage = InMemoryComparatorStorage()

    /** A model with what is saved or, with nothing, its first scenario on screen: Vilafranca and the Colla Vella. */
    private fun makeModel() = ComparatorViewModel(rules, storage).also { model ->
        if (model.state.value.scenarios.isEmpty()) model.show(model.addEmptyScenario().id)
    }

    private val ComparatorViewModel.current get() = state.value.current

    private fun ComparatorViewModel.scenario(id: String) = state.value.scenarios.first { it.id == id }

    @Test
    fun withNothingSavedThereAreNoScenarios() {
        assertEquals(emptyList(), ComparatorViewModel(rules, storage).state.value.scenarios)
    }

    @Test
    fun theFirstScenarioComparesVilafrancaAndTheCollaVella() {
        val model = ComparatorViewModel(rules, storage)

        val scenario = model.addEmptyScenario()

        assertEquals(listOf(scenario.id), model.state.value.scenarios.map { it.id })
        assertEquals(scenario.id, model.current.id)
        assertEquals(listOf("VERDS", "VELLA"), scenario.colles.map { it.shortName })
    }

    @Test
    fun theUntouchedScenarioEveryComparatorStartedWithIsDropped() {
        storage.value = """
            {"scenarios":[{"id":"A","colles":[
                {"id":"V","name":"Vilafranca","shortName":"VERDS","rounds":[null,null,null,null,null],"penalties":0},
                {"id":"C","name":"Colla Vella","shortName":"VELLA","rounds":[null,null,null,null,null],"penalties":0}
            ]}],"currentId":"A"}
        """.trimIndent()

        assertEquals(emptyList(), ComparatorViewModel(rules, storage).state.value.scenarios)
    }

    @Test
    fun anOnlyScenarioWithACastellIsKept() {
        val model = makeModel()
        model.set(d("3de9f"), ComparatorCell(model.current.colles.first().id, round = 0))

        assertEquals(listOf(model.current.id), ComparatorViewModel(rules, storage).state.value.scenarios.map { it.id })
    }

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
    fun theOnlyScenarioCanBeDeletedAndComesBack() {
        val model = makeModel()
        model.rename(model.current.id, "Pla A")
        val only = model.current

        val deleted = assertNotNull(model.delete(only.id))
        assertEquals(emptyList(), model.state.value.scenarios)
        assertEquals(emptyList(), ComparatorViewModel(rules, storage).state.value.scenarios)

        model.restore(deleted)
        assertEquals(only, model.current)
    }

    @Test
    fun aScenarioAfterDeletingThemAllIsTheOneOnScreen() {
        val model = makeModel()
        model.delete(model.current.id)

        val scenario = model.addEmptyScenario()

        assertEquals(scenario.id, model.current.id)
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

    @Test
    fun everyCollaOfTheDirectoryCanBePickedAfterTheContestOnes() {
        assertEquals(118, KnownColla.ALL.size)
        assertEquals(listOf("VERDS", "VELLA"), KnownColla.ALL.take(2).map { it.shortName })
        assertEquals(17, KnownColla.CONTEST.size)
        assertEquals(KnownColla.ALL.size, KnownColla.ALL.map { it.name }.toSet().size)
        assertEquals(KnownColla.ALL.size, KnownColla.ALL.map { it.shortName }.toSet().size)
        assertTrue(KnownColla.ALL.all { it.shortName.length <= 5 })
    }

    @Test
    fun theCollesMatchAnyOfTheirNamesIgnoringAccents() {
        assertEquals(KnownColla.ALL, KnownColla.matching("  "))
        assertEquals(
            listOf("Minyons de l'Arboç", "Minyons de Terrassa", "Santa Cristina d'Aro"),
            KnownColla.matching("minyons").map { it.name },
        )
        assertEquals(listOf("Terrassa"), KnownColla.matching("castellers de terrassa").map { it.name })
        assertEquals(listOf("Gràcia"), KnownColla.matching("vila de gracia").map { it.name })
        assertEquals(listOf("Badalona"), KnownColla.matching("BDN", KnownColla.OTHERS).map { it.name })
    }

    @Test
    fun aCollaTypedByEitherOfItsNamesIsTheKnownOne() {
        assertEquals(KnownColla.named("Badalona"), KnownColla.custom(" castellers de badalona "))
        assertEquals("MINY", KnownColla.custom("Minyons de Terrassa").shortName)
    }
}
