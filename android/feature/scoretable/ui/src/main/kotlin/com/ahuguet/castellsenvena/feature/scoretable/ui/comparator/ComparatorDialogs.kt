package com.ahuguet.castellsenvena.feature.scoretable.ui.comparator

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellNotation
import com.ahuguet.castellsenvena.feature.scoretable.presentation.comparator.KnownColla
import kotlinx.coroutines.launch

/** Asks for a new name for a scenario; a blank one names it after who wins again. */
@Composable
internal fun ScenarioRenameDialog(
    initialName: String,
    placeholder: String,
    onSave: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    var name by rememberSaveable { mutableStateOf(initialName) }
    val focusRequester = remember { FocusRequester() }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Nom de l'escenari") },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Nom") },
                placeholder = { Text(placeholder) },
                supportingText = { Text("Deixa'l buit per mostrar qui guanya.") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences, imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { onSave(name) }),
                modifier = Modifier.focusRequester(focusRequester),
            )
            LaunchedEffect(focusRequester) { focusRequester.requestFocus() }
        },
        confirmButton = { TextButton(onClick = { onSave(name) }) { Text("Desa") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel·la") } },
    )
}

/**
 * Picks the colla for a column, or for a new column: one of the known colles, or any other
 * typed by hand. The colles already in the comparison are disabled.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ComparatorCollaPicker(
    title: String,
    takenNames: Set<String>,
    onPick: (KnownColla) -> Unit,
    onDismiss: () -> Unit,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    var customName by rememberSaveable { mutableStateOf("") }

    fun pick(colla: KnownColla) {
        scope.launch { sheetState.hide() }.invokeOnCompletion { onPick(colla) }
    }

    // Typed by hand, a colla already in the comparison would be a second column for it.
    val isCustomTaken = takenNames.any { it.equals(customName.trim(), ignoreCase = true) }
    val canPickCustom = customName.isNotBlank() && !isCustomTaken

    fun pickCustom() {
        if (canPickCustom) pick(KnownColla.custom(customName))
    }

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        Column {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp),
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedTextField(
                    value = customName,
                    onValueChange = { customName = it },
                    label = { Text("Una altra colla") },
                    supportingText = if (isCustomTaken) ({ Text("Ja és a la comparació") }) else null,
                    isError = isCustomTaken,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Words, imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(onDone = { pickCustom() }),
                    modifier = Modifier.weight(1f),
                )
                TextButton(onClick = ::pickCustom, enabled = canPickCustom) { Text("Afegeix") }
            }
            SectionHeader("Colles")
            LazyColumn(modifier = Modifier.heightIn(max = 480.dp)) {
                items(KnownColla.ALL, key = { it.name }) { known ->
                    ListRow(
                        title = known.name,
                        enabled = known.name !in takenNames,
                        onClick = { pick(known) },
                        trailing = {
                            Text(
                                text = known.shortName,
                                style = MaterialTheme.typography.labelMedium.merge(CastellNotation),
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        },
                    )
                }
            }
        }
    }
}
