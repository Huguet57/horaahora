package com.ahuguet.castellsenvena.feature.agenda.ui.events

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyItemScope
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.ArrowOutward
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.LocalReduceMotion
import com.ahuguet.castellsenvena.core.domain.agenda.AgendaSourceStatus
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.feature.agenda.presentation.groupfilter.AgendaOtherEventsDisclosureState

private val DisclosureSaver = Saver<AgendaOtherEventsDisclosureState, Boolean>(
    save = { it.isExpanded },
    restore = { AgendaOtherEventsDisclosureState(isExpanded = it) },
)

/**
 * The events of the selected day: those of the followed groups first, and the
 * rest behind a disclosure. Without data it offers the official agenda.
 */
@Composable
internal fun AgendaEventList(
    events: List<CastellEvent>,
    otherEvents: List<CastellEvent>,
    isLoading: Boolean,
    errorMessage: String?,
    sourceStatus: AgendaSourceStatus,
    officialUrl: String,
    listState: LazyListState,
    onRetry: () -> Unit,
    onOpenLink: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val reduceMotion = LocalReduceMotion.current
    val hasMatchingEvents = events.isNotEmpty()
    // A different set of other events starts with its own disclosure state.
    val otherEventsSection = "$hasMatchingEvents:" + otherEvents.joinToString("|") { it.id }
    var disclosure by rememberSaveable(otherEventsSection, stateSaver = DisclosureSaver) {
        mutableStateOf(AgendaOtherEventsDisclosureState.initial(hasMatchingEvents))
    }
    fun LazyItemScope.animated(): Modifier = if (reduceMotion) Modifier else Modifier.animateItem()

    LazyColumn(
        state = listState,
        modifier = modifier,
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        when {
            isLoading && events.isEmpty() && otherEvents.isEmpty() -> item(key = "loading") {
                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }

            events.isNotEmpty() || otherEvents.isNotEmpty() -> {
                items(events, key = { "selected:${it.id}" }, contentType = { "event" }) { event ->
                    AgendaEventCard(event = event, onOpenLink = onOpenLink, modifier = animated())
                }
                if (otherEvents.isNotEmpty()) {
                    if (!hasMatchingEvents) {
                        item(key = "no-matching-events") {
                            Text(
                                text = "No hi ha actuacions de les colles seleccionades",
                                style = MaterialTheme.typography.titleSmall,
                                color = CastellsTheme.colors.secondaryText,
                                textAlign = TextAlign.Center,
                                modifier = animated()
                                    .fillMaxWidth()
                                    .padding(vertical = 5.dp),
                            )
                        }
                    }
                    item(key = "other-events") {
                        OtherEventsDisclosure(
                            count = otherEvents.size,
                            isExpanded = disclosure.isExpanded,
                            onToggle = { disclosure = disclosure.toggled() },
                            modifier = animated(),
                        )
                    }
                    if (disclosure.isExpanded) {
                        items(otherEvents, key = { "other:${it.id}" }, contentType = { "event" }) { event ->
                            AgendaEventCard(
                                event = event,
                                onOpenLink = onOpenLink,
                                isOutsideFilter = true,
                                modifier = animated(),
                            )
                        }
                    }
                }
            }

            errorMessage != null -> item(key = "fallback") {
                OfficialAgendaFallback(
                    message = "No s'ha pogut connectar al servidor.",
                    onRetry = onRetry,
                    onOpenOfficialAgenda = { onOpenLink(officialUrl) },
                )
            }

            sourceStatus == AgendaSourceStatus.UNAVAILABLE -> item(key = "fallback") {
                OfficialAgendaFallback(
                    message = "Les dades natives no estan disponibles ara mateix.",
                    onRetry = onRetry,
                    onOpenOfficialAgenda = { onOpenLink(officialUrl) },
                )
            }

            else -> item(key = "empty") {
                Text(
                    text = "No hi ha actuacions aquest dia",
                    style = MaterialTheme.typography.titleSmall,
                    color = CastellsTheme.colors.secondaryText,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 20.dp),
                )
            }
        }
    }
}

@Composable
private fun OtherEventsDisclosure(count: Int, isExpanded: Boolean, onToggle: () -> Unit, modifier: Modifier = Modifier) {
    val color = CastellsTheme.colors.secondaryText
    Row(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(CastellsTheme.colors.card)
            .clickable(
                onClickLabel = if (isExpanded) "Plega les actuacions" else "Mostra les actuacions",
                onClick = onToggle,
            )
            .semantics(mergeDescendants = true) {
                contentDescription = "Altres actuacions del dia"
                stateDescription = "$count, ${if (isExpanded) "desplegades" else "plegades"}"
            }
            .padding(horizontal = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(Icons.AutoMirrored.Filled.List, contentDescription = null, tint = color, modifier = Modifier.size(18.dp))
        Text(
            text = "Altres actuacions del dia · $count",
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.SemiBold,
            color = color,
            modifier = Modifier.weight(1f),
        )
        Icon(
            imageVector = if (isExpanded) Icons.Filled.KeyboardArrowUp else Icons.Filled.KeyboardArrowDown,
            contentDescription = null,
            tint = color,
        )
    }
}

/** Shown when the agenda has no data: the official agenda stays one tap away. */
@Composable
private fun OfficialAgendaFallback(message: String, onRetry: () -> Unit, onOpenOfficialAgenda: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(CastellsTheme.colors.card, RoundedCornerShape(12.dp))
            .padding(start = 14.dp, top = 14.dp, end = 14.dp, bottom = 6.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Icon(
            imageVector = Icons.Filled.WifiOff,
            contentDescription = null,
            tint = CastellsTheme.colors.secondaryText,
            modifier = Modifier.size(22.dp),
        )
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(
                text = "Agenda temporalment no disponible",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
            )
            Text(text = message, style = MaterialTheme.typography.bodySmall, color = CastellsTheme.colors.secondaryText)
            Row {
                TextButton(onClick = onRetry, contentPadding = PaddingValues(end = 12.dp)) {
                    Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Torna-ho a provar")
                }
                TextButton(onClick = onOpenOfficialAgenda, contentPadding = PaddingValues(horizontal = 12.dp)) {
                    Icon(Icons.Filled.ArrowOutward, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Agenda oficial")
                }
            }
        }
    }
}
