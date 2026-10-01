package com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator

import com.ahuguet.castellsenvena.core.common.TextFolding
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

/**
 * A colla the comparison offers to pick, with the short name for narrow columns and the name in
 * the CCCC directory, which the picker also searches.
 */
data class KnownColla(val name: String, val shortName: String, val officialName: String = name) {
    companion object {
        /** The colles of the Concurs de Castells 2026, first. */
        val CONTEST = listOf(
            KnownColla("Vilafranca", "VERDS", "Castellers de Vilafranca"),
            KnownColla("Colla Vella", "VELLA", "Colla Vella dels Xiquets de Valls"),
            KnownColla("Colla Joves", "JOVES", "Colla Joves Xiquets de Valls"),
            KnownColla("Jove de Tarragona", "JOVE", "Colla Jove Xiquets de Tarragona"),
            KnownColla("Barcelona", "CDB", "Castellers de Barcelona"),
            KnownColla("Capgrossos", "CAPS", "Capgrossos de Mataró"),
            KnownColla("Sabadell", "SAB", "Castellers de Sabadell"),
            KnownColla("Xiquets de Tarragona", "XDT"),
            KnownColla("Sant Pere i Sant Pau", "SPSP", "Colla Castellera Sant Pere i Sant Pau"),
            KnownColla("Nens del Vendrell", "NENS"),
            KnownColla("Sant Cugat", "SCG", "Castellers de Sant Cugat"),
            KnownColla("Xiquets de Reus", "REUS"),
            KnownColla("Gràcia", "GRÀC", "Castellers de la Vila de Gràcia"),
            KnownColla("Lleida", "LLEI", "Castellers de Lleida"),
            KnownColla("Moixiganguers", "MOIX", "Moixiganguers d'Igualada"),
            KnownColla("Sants", "SANTS", "Castellers de Sants"),
            KnownColla("Terrassa", "TERR", "Castellers de Terrassa"),
        )

        /** Every other colla of the CCCC directory (castellscat.cat, 2026-07-25), by name. */
        val OTHERS = listOf(
            KnownColla("Al·lots de Llevant", "ALLOT"),
            KnownColla("Alt Maresme", "AMAR", "Colla Castellera de l'Alt Maresme i la Selva Marítima"),
            KnownColla("Altafulla", "ALTA", "Castellers d'Altafulla"),
            KnownColla("Andorra", "AND", "Castellers d'Andorra"),
            KnownColla("Arreplegats", "ARREP", "Arreplegats de la Zona Universitària"),
            KnownColla("Badalona", "BDN", "Castellers de Badalona"),
            KnownColla("Baix Montseny", "BMONT", "Castellers del Baix Montseny"),
            KnownColla("Berga", "BERGA", "Castellers de Berga"),
            KnownColla("Bergants", "BRGNT", "Bergants del Campus de Terrassa"),
            KnownColla("Berlín", "BERL", "Colla Castellera de Berlín"),
            KnownColla("Bordegassos", "BORD", "Bordegassos de Vilanova"),
            KnownColla("Boston", "BOST", "Castellers de Boston"),
            KnownColla("Brivalls", "BRIV", "Brivalls de Cornudella"),
            KnownColla("Brussel·les", "BRUS", "Mannekes de Brussel·les"),
            KnownColla("Caldes", "CALD", "Castellers de Caldes de Montbui"),
            KnownColla("Cambrils", "CAMB", "Xiquets de Cambrils"),
            KnownColla("Castellar", "CTLR", "Castellers de Castellar del Vallès"),
            KnownColla("Castelldefels", "CDF", "Castellers de Castelldefels"),
            KnownColla("Cerdanya", "CDNYA", "Colla Castellera de Cerdanya"),
            KnownColla("Cerdanyola", "CERD", "Castellers de Cerdanyola"),
            KnownColla("Copenhagen", "CPH", "Xiquets de Copenhagen"),
            KnownColla("Cornellà", "CORN", "Castellers de Cornellà"),
            KnownColla("Cubelles", "CUB", "Castellers del Foix de Cubelles"),
            KnownColla("Descargolats", "DESC", "Descargolats de l'EEBE"),
            KnownColla("Edinburgh", "EDI", "Colla Castellera d’Edinburgh"),
            KnownColla("Éire", "ÉIRE", "Castellers d’Éire"),
            KnownColla("El Prat", "PRAT", "Castellers del Prat de Llobregat"),
            KnownColla("Emboirats", "EMBO", "Emboirats de la Universitat de Vic"),
            KnownColla("Encantats de Begues", "ENC", "Colla Castellera Els Encantats de Begues"),
            KnownColla("Engrescats", "ENGR", "Engrescats de la URL"),
            KnownColla("Esparreguera", "ESPAR", "Castellers d'Esparreguera"),
            KnownColla("Esperxats", "ESPX", "Esperxats de l'Estany"),
            KnownColla("Esplugues", "ESPL", "Castellers d'Esplugues"),
            KnownColla("Esquerra de l'Eixample", "EIX", "Colla Castellera de l'Esquerra de l'Eixample"),
            KnownColla("Estocolm", "ESTOC", "Castellers d'Estocolm"),
            KnownColla("Figueres", "FIG", "Colla Castellera de Figueres"),
            KnownColla("Gambirots", "GAMB", "Gambirots de la UIB"),
            KnownColla("Ganàpies", "GANÀ", "Ganàpies de la UAB"),
            KnownColla("Gavà", "GAVÀ", "Colla Castellera de Gavà"),
            KnownColla("Grillats", "GRILL", "Grillats del Campus del Baix Llobregat"),
            KnownColla("Jove de Barcelona", "JBCN", "Colla Castellera Jove de Barcelona"),
            KnownColla("Jove de l'Hospitalet", "HOSP", "Colla Jove de l'Hospitalet"),
            KnownColla("Jove de Sitges", "SITG", "Colla Jove de Castellers de Sitges"),
            KnownColla("L'Adroc", "ADROC", "Castellers de l'Adroc"),
            KnownColla("La Bisbal", "BISB", "Colla Castellera La Bisbal del Penedès"),
            KnownColla("La Selva", "SELVA", "Castellers de la Selva"),
            KnownColla("Laietans", "LAIE", "Laietans de Gramenet"),
            KnownColla("Lausanne", "LAUS", "Castellers de Lausanne"),
            KnownColla("Les Roquetes", "ROQ", "Castellers de les Roquetes"),
            KnownColla("Lluçanès", "LLUÇ", "Castellers del Lluçanès"),
            KnownColla("Llunàtics", "LLUN", "Llunàtics UPC Vilanova"),
            KnownColla("Lo Prado", "PRADO", "Castellers de Lo Prado"),
            KnownColla("Londres", "LON", "Castellers of London"),
            KnownColla("Madrid", "MAD", "Colla Castellera de Madrid"),
            KnownColla("Mallorca", "MALL", "Castellers de Mallorca"),
            KnownColla("Manyacs", "MANY", "Manyacs de Parets"),
            KnownColla("Margeners", "MARG", "Margeners de Guissona"),
            KnownColla("Marrecs", "MARR", "Marrecs de Salt"),
            KnownColla("Matossers", "MATOS", "Matossers de Molins de Rei"),
            KnownColla("Mediona", "MED", "Castellers de Mediona"),
            KnownColla("Minyons de l'Arboç", "ARBOÇ"),
            KnownColla("Minyons de Terrassa", "MINY"),
            KnownColla("Mollet", "MOLL", "Castellers de Mollet"),
            KnownColla("Montcada", "MONTC", "Castellers de Montcada i Reixac"),
            KnownColla("Montreal", "MTL", "Castellers de Montreal"),
            KnownColla("Nois de la Torre", "NOIS"),
            KnownColla("Pallagos", "CONFL", "Pallagos del Conflent"),
            KnownColla("Pallars", "PALL", "Castellers del Pallars"),
            KnownColla("París", "PARÍS", "Castellers de París"),
            KnownColla("Passerells", "PASS", "Passerells del TCM"),
            KnownColla("Pataquers", "PATA", "Pataquers de la URV"),
            KnownColla("Penjats", "PENJ", "Penjats del Campus de Manresa"),
            KnownColla("Poble-sec", "PSEC", "Castellers del Poble Sec"),
            KnownColla("Riberal", "RIB", "Castellers del Riberal"),
            KnownColla("Rubí", "RUBÍ", "Castellers de Rubí"),
            KnownColla("Sagals d'Osona", "SAGAL"),
            KnownColla("Sagrada Família", "SGF", "Castellers de la Sagrada Família"),
            KnownColla("Salats", "SALAT", "Salats de Súria"),
            KnownColla("Sant Adrià", "SADR", "Castellers de Sant Adrià"),
            KnownColla("Sant Feliu", "SFEL", "Castellers de Sant Feliu"),
            KnownColla("Sant Vicenç", "SVIC", "Castellers de Sant Vicenç dels Horts"),
            KnownColla("Santa Coloma", "SCOL", "Castellers de Santa Coloma"),
            KnownColla("Santa Cristina d'Aro", "STCR", "Minyons de Santa Cristina d'Aro"),
            KnownColla("Santpedor", "SPED", "Castellers de Santpedor"),
            KnownColla("Sarrià", "SARR", "Castellers de Sarrià"),
            KnownColla("Serrallo", "SERR", "Xiquets del Serrallo"),
            KnownColla("Sydney", "SYD", "Castellers de Sydney"),
            KnownColla("Tirallongues", "TIRA", "Tirallongues de Manresa"),
            KnownColla("Torraires", "TORRA", "Torraires de Montblanc"),
            KnownColla("Tortosa", "TORT", "Castellers de Tortosa"),
            KnownColla("Trempats", "TREMP", "Trempats de la UPF"),
            KnownColla("Vacarisses", "VAC", "Colla Castellera de Vacarisses"),
            KnownColla("Vailets", "VAIL", "Vailets de Gelida"),
            KnownColla("Vila-seca", "VSECA", "Xiquets de Vila-seca"),
            KnownColla("Viladecans", "VLDC", "Castellers de Viladecans"),
            KnownColla("Xerrics", "OLOT", "Xerrics d'Olot"),
            KnownColla("Xicots", "XICOT", "Xicots de Vilafranca"),
            KnownColla("Xics de Granollers", "GRAN"),
            KnownColla("Xiqüelos del Delta", "DELTA", "Xiqüelos i Xiqüeles del Delta"),
            KnownColla("Xoriguers", "XORI", "Xoriguers de la UdG"),
            KnownColla("Zürich", "ZÜR", "Castellers de Zürich"),
        )

        val ALL = CONTEST + OTHERS

        /**
         * The colles whose name, short name or name in the directory contains [query], ignoring
         * case and accents; all of them without a query.
         */
        fun matching(query: String, colles: List<KnownColla> = ALL): List<KnownColla> {
            if (query.isBlank()) return colles
            return colles.filter { known ->
                listOf(known.name, known.shortName, known.officialName)
                    .any { TextFolding.containsIgnoringCaseAndAccents(it, query.trim()) }
            }
        }

        /** The colla called [name], by either of its names, ignoring case and accents. */
        fun named(name: String): KnownColla? {
            val folded = TextFolding.fold(name.trim())
            return ALL.firstOrNull { TextFolding.fold(it.name) == folded || TextFolding.fold(it.officialName) == folded }
        }

        /**
         * A colla typed by hand: the known one with that name or, otherwise, its last word, up
         * to five letters, in capitals.
         */
        fun custom(name: String): KnownColla {
            val trimmed = name.trim()
            named(trimmed)?.let { return it }
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
    val currentId: String?,
) {
    /** Without scenarios, one without colles, which no screen shows. */
    val current: ComparatorScenario
        get() = scenarios.firstOrNull { it.id == currentId } ?: scenarios.firstOrNull() ?: NO_SCENARIO
    val favorites: List<ComparatorScenario> get() = scenarios.filter { it.isFavorite }
    val others: List<ComparatorScenario> get() = scenarios.filterNot { it.isFavorite }

    private companion object {
        val NO_SCENARIO = ComparatorScenario(id = "", colles = emptyList())
    }
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
        val colles = mutableState.value.scenarios.firstOrNull()?.colles?.map { it.cleared() } ?: firstColles()
        val scenario = ComparatorScenario(id = newId(), colles = colles)
        update { it.copy(scenarios = it.scenarios + scenario) }
        return scenario
    }

    /** Removes a scenario; [restore] puts it back. */
    fun delete(id: String): DeletedScenario? {
        val state = mutableState.value
        val index = state.scenarios.indexOfFirst { it.id == id }
        if (index < 0) return null
        val scenarios = state.scenarios.toMutableList()
        val removed = scenarios.removeAt(index)
        val currentId = if (id == state.currentId) scenarios.getOrNull(minOf(index, scenarios.lastIndex))?.id else state.currentId
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
            ?.takeUnless { isUntouchedStart(it.scenarios) }
            ?: return ComparatorState(emptyList(), null)
        // Favourites first, as the list shows them, and the known colles with today's short
        // name, which may have changed since they were saved.
        val loaded = stored.scenarios.map(::refreshingShortNames)
        val currentId = stored.currentId.takeIf { id -> loaded.any { it.id == id } } ?: loaded.firstOrNull()?.id
        return ComparatorState(loaded.filter { it.isFavorite } + loaded.filterNot { it.isFavorite }, currentId)
    }

    /** Vilafranca and the Colla Vella, the colles of the first scenario. */
    private fun firstColles(): List<ComparatorColla> =
        KnownColla.ALL.take(2).map { ComparatorColla(id = newId(), name = it.name, shortName = it.shortName) }

    /**
     * Whether the scenarios are just the one every comparator used to start with, as it was: the
     * list now starts empty, and creating the first scenario gives the same one.
     */
    private fun isUntouchedStart(scenarios: List<ComparatorScenario>): Boolean {
        val scenario = scenarios.singleOrNull() ?: return false
        return !scenario.isFavorite && scenario.name == null &&
            scenario.colles.map { it.name } == KnownColla.ALL.take(2).map { it.name } &&
            scenario.colles.all { it == it.cleared() }
    }

    private fun refreshingShortNames(scenario: ComparatorScenario): ComparatorScenario = scenario.copy(
        colles = scenario.colles.map { colla ->
            KnownColla.ALL.firstOrNull { it.name == colla.name }?.let { colla.copy(shortName = it.shortName) } ?: colla
        },
    )

    private fun newId(): String = UUID.randomUUID().toString()

    @Serializable
    private data class Stored(val scenarios: List<ComparatorScenario>, val currentId: String? = null)

    companion object {
        const val MAX_COLLES = 4
        const val STORAGE_KEY = "comparator.scenarios.v1"
        private const val DEFAULT_ANCHOR = "3de9f"

        private val json = Json { ignoreUnknownKeys = true }
    }
}
