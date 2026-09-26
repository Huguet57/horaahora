package com.ahuguet.castellsenvena.feature.agenda.ui.events

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowOutward
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.core.domain.agenda.CastellEvent
import com.ahuguet.castellsenvena.feature.agenda.presentation.googleMapsSearchUrl

@Composable
internal fun AgendaEventCard(
    event: CastellEvent,
    onOpenLink: (String) -> Unit,
    modifier: Modifier = Modifier,
    isOutsideFilter: Boolean = false,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .semantics(mergeDescendants = true) {
                if (isOutsideFilter) stateDescription = "Aquesta actuació no coincideix amb el filtre"
            },
        shape = RoundedCornerShape(14.dp),
        color = CastellsTheme.colors.card,
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.Schedule, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    text = event.timeLabel,
                    style = MaterialTheme.typography.titleSmall.merge(TabularNumbers),
                    fontWeight = FontWeight.SemiBold,
                )
                Spacer(Modifier.weight(1f))
                Text(
                    text = event.municipality,
                    style = MaterialTheme.typography.bodyMedium,
                    color = CastellsTheme.colors.secondaryText,
                )
            }

            Text(text = event.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)

            if (event.venue.isNotEmpty()) {
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .clickable(onClickLabel = "Obre ${event.venue} a Google Maps") {
                            onOpenLink(googleMapsSearchUrl(event.venue, event.municipality))
                        }
                        .padding(vertical = 2.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Place,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = event.venue,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }

            if (event.participatingGroups.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    for (group in event.participatingGroups) {
                        Text(text = "• $group", style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }

            if (event.notes.isNotEmpty()) {
                Text(
                    text = event.notes,
                    style = MaterialTheme.typography.bodySmall,
                    color = CastellsTheme.colors.secondaryText,
                )
            }

            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = event.attribution,
                    style = MaterialTheme.typography.labelSmall,
                    color = CastellsTheme.colors.secondaryText,
                    modifier = Modifier.weight(1f),
                )
                IconButton(onClick = { onOpenLink(event.sourceUrl) }, modifier = Modifier.size(32.dp)) {
                    Icon(
                        imageVector = Icons.Filled.ArrowOutward,
                        contentDescription = "Obre l'agenda oficial",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(16.dp),
                    )
                }
            }
        }
    }
}
