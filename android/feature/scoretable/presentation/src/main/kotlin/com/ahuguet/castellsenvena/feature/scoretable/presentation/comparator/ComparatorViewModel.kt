package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import java.util.UUID
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** A cell of the grid: one colla in one round. */
data class ComparatorCell(val collaId: String, val round: Int) {
    val key: String get() = "$collaId-$round"
}

/** A colla the comparison offers to pick, with the short name for narrow columns. */
data class KnownColla(val name: String, val shortName: String) {
    companion object {
        val ALL = listOf(
            KnownColla("Vilafranca", "VERDS"),
            KnownColla("Colla Vella", "VELLA"),
            KnownColla("Colla Joves", "JOVES"),
            KnownColla("Jove de Tarragona", "JOVE"),
            KnownColla("Barcelona", "CDB"),
            KnownColla("Capgrossos", "CAPS"),
            KnownColla("Sabadell", "SAB"),
            KnownColla("Xiquets de Tarragona", "XDT"),
            KnownColla("Sant Pere i Sant Pau", "SPSP"),
            KnownColla("Nens del Vendrell", "NENS"),
            KnownColla("Sant Cugat", "SCG"),
            KnownColla("Xiquets de Reus", "REUS"),
            KnownColla("Gràcia", "GRÀC"),
            KnownColla("Lleida", "LLEI"),
            KnownColla("Moixiganguers", "MOIX"),
            KnownColla("Sants", "SANTS"),
            KnownColla("Terrassa", "TERR"),
        )

        /** A colla typed by hand: its last word, up to five letters, in capitals. */
        fun custom(name: String): KnownColla {
            val trimmed = name.trim()
            val lastWord = trimmed.split(' ').lastOrNull { it.isNotEmpty() } ?: trimmed
            return KnownColla(trimmed, lastWord.take(5).uppercase())
        }
    }
}

/** Where the scenarios are kept between launches: the app backs it with its preferences. */
interface ComparatorStorage {
    fun load(): String?
    fun save(value: String)
}

class InMemoryComparatorStorage(var value: String? = null) : ComparatorStorage {
    override fun load(): String? = value

    override fun save(value: String) {
        this.value = value
    }
}

data class ComparatorState(
    /** The favourites first, in the order the list shows them. */
    val scenarios: List<ComparatorScenario>,
    /** The scenario whose grid is open, or opens next. */
    val currentId: String,
) {
    val current: ComparatorScenario get() = scenarios.firstOrNull { it.id == currentId } ?: scenarios.first()
    val favorites: List<ComparatorScenario> get() = scenarios.filter { it.isFavorite }
    val others: List<ComparatorScenario> get() = scenarios.filterNot { it.isFavorite }
}

/** A deleted scenario and where it was, to put it back. */
data class DeletedScenario(val scenario: ComparatorScenario, val index: Int)

/**
 * The scenarios of the comparator and the one on screen. Every change is saved at once; the
 * colles belong to each scenario, so changing them only changes the scenario on screen.
 */
class ComparatorViewModel(val rules: ComparatorRules, private val storage: ComparatorStorage) {
    private val mutableState = MutableStateFlow(load())
    val state: StateFlow<ComparatorState> = mutableState.asStateFlow()

    private val current: ComparatorScenario get() = mutableState.value.current

    // Scenarios

    fun show(id: String) {
        if (mutableState.value.scenarios.any { it.id == id }) update { it.copy(currentId = id) }
    }

    /**
     * Puts a copy right after the scenario, or on top of the rest for a favourite: a copy is
     * never a favourite itself, nor keeps the name.
     */
    fun duplicate(id: String): ComparatorScenario? {
        val state = mutableState.value
        val index = state.scenarios.indexOfFirst { it.id == id }
        if (index < 0) return null
        val original = state.scenarios[index]
        val copy = original.copy(id = newId(), isFavorite = false, name = null)
        val at = if (original.isFavorite) state.favorites.size else index + 1
        update { it.copy(scenarios = it.scenarios.toMutableList().apply { add(at, copy) }) }
        return copy
    }

    fun duplicateCurrent() {
        duplicate(current.id)?.let { show(it.id) }
    }

    /** A blank name clears it. */
    fun rename(id: String, name: String) {
        val trimmed = name.trim().ifEmpty { null }
        updateScenario(id) { it.copy(name = trimmed) }
    }

    /**
     * A new favourite goes last among the favourites; an old one, first among the rest. Both
     * are the place right after the other favourites.
     */
    fun toggleFavorite(id: String) {
        update { state ->
            val scenarios = state.scenarios.toMutableList()
            val index = scenarios.indexOfFirst { it.id == id }
            if (index < 0) return@update state
            val moved = scenarios.removeAt(index).let { it.copy(isFavorite = !it.isFavorite) }
            scenarios.add(scenarios.count { it.isFavorite }, moved)
            state.copy(scenarios = scenarios)
        }
    }

    /** Moves a scenario within the favourites or the rest, from one position to another. */
    fun moveScenario(favorites: Boolean, from: Int, to: Int) {
        update { state ->
            val group = (if (favorites) state.favorites else state.others).toMutableList()
            if (from !in group.indices || to !in group.indices || from == to) return@update state
            group.add(to, group.removeAt(from))
            state.copy(scenarios = if (favorites) group + state.others else state.favorites + group)
        }
    }

    /** A scenario with the colles of the first one and every round empty, at the end. */
    fun addEmptyScenario(): ComparatorScenario {
        val colles = mutableState.value.scenarios.firstOrNull()?.colles.orEmpty().map { it.cleared() }
        val scenario = ComparatorScenario(id = newId(), colles = colles)
        update { it.copy(scenarios = it.scenarios + scenario) }
        return scenario
    }

    /** Removes a scenario, unless it is the only one; [restore] puts it back. */
    fun delete(id: String): DeletedScenario? {
        val state = mutableState.value
        val index = state.scenarios.indexOfFirst { it.id == id }
        if (state.scenarios.size <= 1 || index < 0) return null
        val scenarios = state.scenarios.toMutableList()
        val removed = scenarios.removeAt(index)
        val currentId = if (id == state.currentId) scenarios[minOf(index, scenarios.lastIndex)].id else state.currentId
        update { ComparatorState(scenarios, currentId) }
        return DeletedScenario(removed, index)
    }

    /** Puts back a scenario that [delete] or [clearCurrent] took away, as it was. */
    fun restore(deleted: DeletedScenario) {
        update { state ->
            val scenarios = state.scenarios.toMutableList()
            val existing = scenarios.indexOfFirst { it.id == deleted.scenario.id }
            if (existing >= 0) {
                scenarios[existing] = deleted.scenario
            } else {
                scenarios.add(deleted.index.coerceIn(0, scenarios.size), deleted.scenario)
            }
            // A favourite back among the rest, or the other way round, keeps the sections apart.
            state.copy(scenarios = scenarios.filter { it.isFavorite } + scenarios.filterNot { it.isFavorite })
        }
    }

    /** Empties every round of the scenario on screen, keeping its colles; [restore] undoes it. */
    fun clearCurrent(): DeletedScenario {
        val state = mutableState.value
        val before = DeletedScenario(state.current, state.scenarios.indexOf(state.current))
        updateScenario(before.scenario.id) { scenario -> scenario.copy(colles = scenario.colles.map { it.cleared() }) }
        return before
    }

    // Colles

    fun colla(id: String): ComparatorColla? = current.colles.firstOrNull { it.id == id }

    /** Whether another colla of the scenario on screen is already called [name]. */
    fun isCollaTaken(name: String, exceptId: String? = null): Boolean =
        current.colles.any { it.id != exceptId && it.name.equals(name.trim(), ignoreCase = true) }

    /** Adds a column, unless the scenario is full or already has that colla. */
    fun addColla(known: KnownColla) {
        if (current.colles.size >= MAX_COLLES || isCollaTaken(known.name)) return
        updateScenario(current.id) {
            it.copy(colles = it.colles + ComparatorColla(id = newId(), name = known.name, shortName = known.shortName))
        }
    }

    /** Changes a column's colla, unless another column already has it. */
    fun replaceColla(id: String, known: KnownColla) {
        if (isCollaTaken(known.name, exceptId = id)) return
        updateColla(id) { it.copy(name = known.name, shortName = known.shortName) }
    }

    fun removeColla(id: String) {
        if (current.colles.size <= 1) return
        updateScenario(current.id) { scenario -> scenario.copy(colles = scenario.colles.filterNot { it.id == id }) }
    }

    fun changePenalties(id: String, delta: Int) {
        updateColla(id) { it.copy(penalties = maxOf(0, it.penalties + delta)) }
    }

    // Cells

    fun castell(cell: ComparatorCell): PlannedCastell? = colla(cell.collaId)?.rounds?.getOrNull(cell.round)

    fun set(castell: PlannedCastell?, cell: ComparatorCell) {
        updateColla(cell.collaId) { colla ->
            colla.copy(rounds = colla.rounds.toMutableList().also { it[cell.round] = castell })
        }
    }

    /** Puts the next allowed castell up (`direction > 0`) or down in points in the cell. */
    fun step(cell: ComparatorCell, direction: Int) {
        val colla = colla(cell.collaId) ?: return
        val castell = colla.rounds[cell.round] ?: return
        rules.step(castell, cell.round, colla, direction)?.let { set(it, cell) }
    }

    fun setOutcome(outcome: ComparatorOutcome, cell: ComparatorCell) {
        val castell = castell(cell) ?: return
        set(castell.copy(outcome = outcome), cell)
    }

    /**
     * Where the castell list opens for a cell: its own castell, else the rival's in that round,
     * else the colla's own last one, else any castell of the comparison.
     */
    fun anchor(cell: ComparatorCell): String {
        castell(cell)?.let { return it.notation }
        val colles = current.colles
        return colles.filter { it.id != cell.collaId }.firstNotNullOfOrNull { it.rounds[cell.round] }?.notation
            ?: colla(cell.collaId)?.rounds?.take(cell.round)?.lastOrNull { it != null }?.notation
            ?: colles.firstNotNullOfOrNull { colla -> colla.rounds.firstOrNull { it != null } }?.notation
            ?: DEFAULT_ANCHOR
    }

    // State and storage

    private fun updateColla(id: String, change: (ComparatorColla) -> ComparatorColla) {
        updateScenario(current.id) { scenario ->
            scenario.copy(colles = scenario.colles.map { if (it.id == id) change(it) else it })
        }
    }

    private fun updateScenario(id: String, change: (ComparatorScenario) -> ComparatorScenario) {
        update { state -> state.copy(scenarios = state.scenarios.map { if (it.id == id) change(it) else it }) }
    }

    private fun update(change: (ComparatorState) -> ComparatorState) {
        val old = mutableState.value
        val new = change(old)
        if (new == old) return
        mutableState.value = new
        storage.save(json.encodeToString(Stored.serializer(), Stored(new.scenarios, new.currentId)))
    }

    private fun load(): ComparatorState {
        val stored = storage.load()
            ?.let { runCatching { json.decodeFromString(Stored.serializer(), it) }.getOrNull() }
            ?.takeIf { it.scenarios.isNotEmpty() }
        if (stored == null) {
            val first = ComparatorScenario(
                id = newId(),
                colles = listOf(
                    ComparatorColla(id = newId(), name = "Vilafranca", shortName = "VERDS"),
                    ComparatorColla(id = newId(), name = "Colla Vella", shortName = "VELLA"),
                ),
            )
            return ComparatorState(listOf(first), first.id)
        }
        // Favourites first, as the list shows them, and the known colles with today's short
        // name, which may have changed since they were saved.
        val loaded = stored.scenarios.map(::refreshingShortNames)
        val currentId = stored.currentId.takeIf { id -> loaded.any { it.id == id } } ?: loaded.first().id
        return ComparatorState(loaded.filter { it.isFavorite } + loaded.filterNot { it.isFavorite }, currentId)
    }

    private fun refreshingShortNames(scenario: ComparatorScenario): ComparatorScenario = scenario.copy(
        colles = scenario.colles.map { colla ->
            KnownColla.ALL.firstOrNull { it.name == colla.name }?.let { colla.copy(shortName = it.shortName) } ?: colla
        },
    )

    private fun newId(): String = UUID.randomUUID().toString()

    @Serializable
    private data class Stored(val scenarios: List<ComparatorScenario>, val currentId: String)

    companion object {
        const val MAX_COLLES = 4
        const val STORAGE_KEY = "comparator.scenarios.v1"
        private const val DEFAULT_ANCHOR = "3de9f"

        private val json = Json { ignoreUnknownKeys = true }
    }
}
