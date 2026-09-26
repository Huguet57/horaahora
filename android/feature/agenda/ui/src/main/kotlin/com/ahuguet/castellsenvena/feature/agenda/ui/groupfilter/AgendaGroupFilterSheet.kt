package com.ahuguet.castellsenvena.feature.agenda.ui.groupfilter

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Groups
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconToggleButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ContentUnavailable
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedCard
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedDivider
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedRow
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedSectionFooter
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedSectionHeader
import com.ahuguet.castellsenvena.core.designsystem.component.groupedItemShape
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.feature.agenda.presentation.AgendaViewModel
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaGroupFilterState
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.groupMatchesSearch
import kotlinx.coroutines.launch

/**
 * Chooses the groups the Agenda and the news notifications follow, and the
 * groups featured at the top of the list.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun AgendaGroupFilterSheet(
    model: AgendaViewModel,
    filter: AgendaGroupFilterState,
    directoryErrorMessage: String?,
    onDismiss: () -> Unit,
) {
    val sheetState = rememberModalBottomSheetState()
    val scope = rememberCoroutineScope()
    var query by rememberSaveable { mutableStateOf("") }
    val reloadDirectory: () -> Unit = { scope.launch { model.loadGroupDirectory(forceRefresh = true) } }
    val close: () -> Unit = {
        scope.launch { sheetState.hide() }.invokeOnCompletion { onDismiss() }
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = CastellsTheme.colors.groupedBackground,
    ) {
        Box(modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp)) {
            Text(
                text = "Filtra per colles",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier
                    .align(Alignment.Center)
                    .semantics { heading() },
            )
            TextButton(onClick = close, modifier = Modifier.align(Alignment.CenterEnd)) {
                Text("Fet", fontWeight = FontWeight.SemiBold)
            }
        }

        if (filter.availableGroups.isEmpty()) {
            ContentUnavailable(
                icon = Icons.Outlined.Groups,
                title = "Directori no disponible",
                description = "Les actuacions continuen visibles mentre se segueixen totes les colles.",
                action = { Button(onClick = reloadDirectory) { Text("Torna-ho a provar") } },
                modifier = Modifier.height(360.dp),
            )
        } else {
            GroupSearchField(
                query = query,
                onQueryChange = { query = it },
                // The results need room above the keyboard.
                onFocused = { scope.launch { sheetState.expand() } },
            )
            val results = remember(filter.availableGroups, query) {
                if (query.isBlank()) emptyList() else filter.availableGroups.filter { groupMatchesSearch(it, query) }
            }
            LazyColumn(contentPadding = PaddingValues(bottom = 32.dp)) {
                val rowActions = GroupRowActions(
                    filter = filter,
                    onToggleFollowing = { name -> model.setFollowing(!model.isFollowing(name), name) },
                    onToggleFeatured = { name -> model.setFeatured(!model.isFeatured(name), name) },
                )
                if (query.isBlank()) {
                    item(key = "bulk:all") {
                        GroupedCard(modifier = Modifier.padding(top = 8.dp)) {
                            BulkSelectionRow(
                                title = "Totes les colles",
                                isSelected = !filter.isActive,
                                onClick = model::toggleFollowingAllGroups,
                            )
                        }
                    }
                    if (filter.featuredGroups.isNotEmpty()) {
                        item(key = "header:featured") { GroupedSectionHeader("Colles destacades") }
                        item(key = "bulk:featured") {
                            GroupCell(shape = groupedItemShape(0, filter.featuredGroups.size + 1), showsDivider = true) {
                                BulkSelectionRow(
                                    title = "Totes les destacades",
                                    isSelected = filter.areAllFeaturedGroupsFollowed,
                                    onClick = model::toggleFollowingFeaturedGroups,
                                )
                            }
                        }
                        groupRows(filter.featuredGroups, keyPrefix = "featured", actions = rowActions, leadingRows = 1)
                    }
                    item(key = "header:all") { GroupedSectionHeader("Totes les colles") }
                    groupRows(filter.availableGroups, keyPrefix = "all", actions = rowActions)
                } else {
                    item(key = "header:results") { GroupedSectionHeader("Resultats") }
                    if (results.isEmpty()) {
                        item(key = "no-results") {
                            GroupedCard {
                                Text(
                                    text = "No s'ha trobat cap colla",
                                    color = CastellsTheme.colors.secondaryText,
                                    modifier = Modifier.padding(16.dp),
                                )
                            }
                        }
                    } else {
                        groupRows(results, keyPrefix = "result", actions = rowActions)
                    }
                }

                if (directoryErrorMessage != null) {
                    item(key = "directory-error") {
                        Column(modifier = Modifier.padding(top = 24.dp)) {
                            GroupedCard {
                                GroupedRow(
                                    title = "Torna a carregar el directori",
                                    titleColor = MaterialTheme.colorScheme.primary,
                                    onClick = reloadDirectory,
                                )
                            }
                            GroupedSectionFooter(
                                "No s'ha pogut actualitzar el directori. Es mostra l'última còpia disponible.",
                            )
                        }
                    }
                }
            }
        }
    }
}

private class GroupRowActions(
    val filter: AgendaGroupFilterState,
    val onToggleFollowing: (String) -> Unit,
    val onToggleFeatured: (String) -> Unit,
)

/** Group rows inside one card; [leadingRows] rows of the card come before them. */
private fun LazyListScope.groupRows(
    groups: List<String>,
    keyPrefix: String,
    actions: GroupRowActions,
    leadingRows: Int = 0,
) {
    val count = groups.size + leadingRows
    itemsIndexed(groups, key = { _, name -> "$keyPrefix:$name" }, contentType = { _, _ -> "group" }) { index, name ->
        val position = index + leadingRows
        GroupCell(shape = groupedItemShape(position, count), showsDivider = position < count - 1) {
            GroupFilterRow(
                name = name,
                isFollowing = actions.filter.isFollowing(name),
                isFeatured = actions.filter.isFeatured(name),
                onToggleFollowing = { actions.onToggleFollowing(name) },
                onToggleFeatured = { actions.onToggleFeatured(name) },
            )
        }
    }
}

@Composable
private fun GroupCell(shape: Shape, showsDivider: Boolean, content: @Composable () -> Unit) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = shape,
        color = CastellsTheme.colors.groupedCard,
    ) {
        Column {
            content()
            if (showsDivider) GroupedDivider(startIndent = 56.dp)
        }
    }
}

@Composable
private fun GroupFilterRow(
    name: String,
    isFollowing: Boolean,
    isFeatured: Boolean,
    onToggleFollowing: () -> Unit,
    onToggleFeatured: () -> Unit,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Row(
            modifier = Modifier
                .weight(1f)
                .toggleable(value = isFollowing, role = Role.Checkbox, onValueChange = { onToggleFollowing() })
                .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Checkbox(checked = isFollowing, onCheckedChange = null, modifier = Modifier.padding(12.dp))
            Text(text = name, style = MaterialTheme.typography.bodyLarge)
        }
        IconToggleButton(checked = isFeatured, onCheckedChange = { onToggleFeatured() }) {
            Icon(
                imageVector = if (isFeatured) Icons.Filled.Star else Icons.Outlined.StarOutline,
                contentDescription = if (isFeatured) "Treu $name de colles destacades" else "Destaca $name",
                tint = if (isFeatured) CastellsTheme.colors.star else CastellsTheme.colors.secondaryText,
            )
        }
    }
}

@Composable
private fun BulkSelectionRow(title: String, isSelected: Boolean, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .toggleable(value = isSelected, role = Role.Checkbox, onValueChange = { onClick() })
            .padding(start = 4.dp, end = 16.dp, top = 2.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(checked = isSelected, onCheckedChange = null, modifier = Modifier.padding(12.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.bodyLarge,
            color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
        )
    }
}

@Composable
private fun GroupSearchField(query: String, onQueryChange: (String) -> Unit, onFocused: () -> Unit) {
    val focusManager = LocalFocusManager.current
    TextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .onFocusChanged { if (it.isFocused) onFocused() },
        placeholder = { Text("Cerca una colla") },
        leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
        trailingIcon = if (query.isEmpty()) {
            null
        } else {
            {
                IconButton(onClick = { onQueryChange("") }) {
                    Icon(Icons.Filled.Close, contentDescription = "Esborra la cerca")
                }
            }
        },
        singleLine = true,
        shape = RoundedCornerShape(12.dp),
        colors = TextFieldDefaults.colors(
            focusedContainerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
            unfocusedContainerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
            focusedIndicatorColor = Color.Transparent,
            unfocusedIndicatorColor = Color.Transparent,
        ),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search, autoCorrectEnabled = false),
        keyboardActions = KeyboardActions(onSearch = { focusManager.clearFocus() }),
    )
}
