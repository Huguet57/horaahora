package com.ahuguet.castellsenvena.feature.scoretable.ui

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListLayoutInfo
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.State
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreBarAxis
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTable
import com.ahuguet.castellsenvena.feature.scoretable.presentation.ScoreTableCastell
import com.ahuguet.castellsenvena.feature.scoretable.presentation.notationsBelowWhoseUnloadedBeats
import com.ahuguet.castellsenvena.feature.scoretable.presentation.sectionsByPoints

private const val HEADER_KEY_PREFIX = "grup:"

/** How far below the list a bar keeps pulling the scale while it enters. */
private val FadeBelow = 40.dp

/**
 * The official score table, from the castell worth the most to the one worth the
 * least. The bars zoom to the rows on screen: the smallest value there starts
 * near the left and the largest fills the width, so that neighbouring castells
 * compare at a glance. Tapping a castell marks the ones below it whose
 * descarregat beats its carregat.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScoreTableScreen(modifier: Modifier = Modifier) {
    val table = remember { runCatching { ScoreTable.bundled() }.getOrNull() }
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(title = { Text("Puntuacions") }, scrollBehavior = scrollBehavior)
        },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
        ) {
            if (table == null) {
                ContentUnavailable(icon = Icons.Filled.Warning, title = "No s'ha pogut obrir la taula")
            } else {
                ScoreTableList(
                    table = table,
                    // The top bar takes its scrolled color while the table is under it.
                    modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
                )
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ScoreTableList(table: ScoreTable, modifier: Modifier = Modifier) {
    val sections = remember(table) { table.sectionsByPoints }
    val castells = remember(table) { table.castells.associateBy { it.notation } }
    var selectedNotation by rememberSaveable { mutableStateOf<String?>(null) }
    val selected = selectedNotation?.let(castells::get)
    val winners = remember(table, selected) {
        selected?.let { table.notationsBelowWhoseUnloadedBeats(loadedOf = it).toSet() } ?: emptySet()
    }
    val listState = rememberLazyListState()
    val density = LocalDensity.current
    val scale: State<BarScale> = remember(table, listState, density) {
        val initial = BarScale(ScoreBarAxis.forCastells(table.castells), wholeRows = table.castells.map { it.notation }.toSet())
        derivedStateOf {
            visibleScale(
                layoutInfo = listState.layoutInfo,
                castells = castells,
                fadeBelow = with(density) { FadeBelow.toPx() },
            ) ?: initial
        }
    }

    LazyColumn(state = listState, modifier = modifier.fillMaxSize()) {
        for (section in sections) {
            stickyHeader(key = HEADER_KEY_PREFIX + section.key, contentType = "header") {
                ScoreTableSectionHeader(group = section.group)
            }
            items(section.castells, key = { it.notation }, contentType = { "castell" }) { castell ->
                ScoreTableRow(
                    castell = castell,
                    scale = scale,
                    highlight = when {
                        castell.notation == selectedNotation -> ScoreTableHighlight.Selected
                        castell.notation in winners -> ScoreTableHighlight.BeatsSelectedLoaded(selectedNotation.orEmpty())
                        else -> ScoreTableHighlight.None
                    },
                    onClick = {
                        selectedNotation = if (castell.notation == selectedNotation) null else castell.notation
                    },
                )
            }
        }
        item(key = "font", contentType = "font") {
            Text(
                text = "Taula oficial de puntuacions del Concurs de Castells 2026.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 16.dp),
            )
        }
    }
}

/**
 * The bar scale and the rows whole in the window, the only ones that draw their
 * bar: a row sliding under the group header counts less in the scale, so its bar
 * could overflow.
 */
internal data class BarScale(val axis: ScoreBarAxis, val wholeRows: Set<String>)

/**
 * The scale for the castells on screen. The group header pinned at the top hides
 * the rows under it, so the window starts below it, and a row passing under the
 * header counts less and less until it is gone.
 */
private fun visibleScale(
    layoutInfo: LazyListLayoutInfo,
    castells: Map<String, ScoreTableCastell>,
    fadeBelow: Float,
): BarScale? {
    val items = layoutInfo.visibleItemsInfo
    val headerHeight = items.firstOrNull { (it.key as? String)?.startsWith(HEADER_KEY_PREFIX) == true }?.size ?: 0
    val windowTop = (layoutInfo.viewportStartOffset + headerHeight).toFloat()
    val windowBottom = layoutInfo.viewportEndOffset.toFloat()
    val weighted = items.mapNotNull { item ->
        val castell = castells[item.key as? String] ?: return@mapNotNull null
        castell to ScoreBarAxis.weight(
            rowTop = item.offset.toFloat(),
            windowTop = windowTop,
            windowBottom = windowBottom,
            fadeAbove = headerHeight.toFloat(),
            fadeBelow = fadeBelow,
        )
    }
    val axis = ScoreBarAxis.forVisible(weighted) ?: return null
    return BarScale(axis, wholeRows = weighted.filter { (_, weight) -> weight >= 1.0 }.map { (castell, _) -> castell.notation }.toSet())
}
