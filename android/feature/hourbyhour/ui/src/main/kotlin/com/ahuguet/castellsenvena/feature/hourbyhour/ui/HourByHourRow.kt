package com.ahuguet.castellsenvena.feature.hourbyhour.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.ArrowOutward
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.common.CatalanDates
import com.ahuguet.castellsenvena.core.designsystem.component.GroupedDivider
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.core.domain.hourbyhour.HourByHourItem
import java.time.ZoneId
import kotlinx.coroutines.launch

@Composable
internal fun HourByHourRow(
    item: HourByHourItem,
    zone: ZoneId,
    shape: Shape,
    showsDivider: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val opensLink = item.associatedUrl != null
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = shape,
        color = CastellsTheme.colors.groupedCard,
    ) {
        Column {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(
                        onClickLabel = if (opensLink) {
                            "Obre el contingut de ${item.attribution}"
                        } else {
                            "Mostra el text complet dins l'app"
                        },
                        onClick = onClick,
                    )
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val publishedAt = item.publishedAt
                    if (publishedAt != null) {
                        Text(
                            text = CatalanDates.time(publishedAt.atZone(zone).toLocalTime()),
                            style = MaterialTheme.typography.labelMedium.merge(TabularNumbers),
                            color = CastellsTheme.colors.secondaryText,
                        )
                    }
                    Spacer(Modifier.weight(1f))
                    Text(
                        text = item.attribution,
                        style = MaterialTheme.typography.labelSmall,
                        color = CastellsTheme.colors.secondaryText,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Spacer(Modifier.width(4.dp))
                    Icon(
                        imageVector = if (opensLink) {
                            Icons.Filled.ArrowOutward
                        } else {
                            Icons.AutoMirrored.Filled.KeyboardArrowRight
                        },
                        contentDescription = null,
                        tint = CastellsTheme.colors.tertiaryText,
                        modifier = Modifier.size(14.dp),
                    )
                }
                Text(
                    text = item.displayTitle,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                if (item.summary.isNotEmpty()) {
                    Text(
                        text = item.summary,
                        style = MaterialTheme.typography.bodyMedium,
                        color = CastellsTheme.colors.secondaryText,
                        maxLines = 3,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            if (showsDivider) GroupedDivider()
        }
    }
}

/** The full text of an item without its own link. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun HourByHourDetailSheet(item: HourByHourItem, zone: ZoneId, onDismiss: () -> Unit) {
    val sheetState = rememberModalBottomSheetState()
    val scope = rememberCoroutineScope()
    val close: () -> Unit = {
        scope.launch { sheetState.hide() }.invokeOnCompletion { onDismiss() }
    }

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 24.dp, end = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "Hora a Hora",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f),
            )
            IconButton(onClick = close) {
                Icon(Icons.Filled.Close, contentDescription = "Tanca")
            }
        }
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(start = 24.dp, end = 24.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            val publishedAt = item.publishedAt?.atZone(zone)
            if (publishedAt != null) {
                Text(
                    text = "${CatalanDates.fullDate(publishedAt.toLocalDate())} · " +
                        CatalanDates.time(publishedAt.toLocalTime()),
                    style = MaterialTheme.typography.bodyMedium.merge(TabularNumbers),
                    color = CastellsTheme.colors.secondaryText,
                )
            }
            Text(
                text = item.displayTitle,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
            )
            if (item.summary.isNotEmpty()) {
                HorizontalDivider()
                SelectionContainer {
                    Text(
                        text = item.summary,
                        style = MaterialTheme.typography.bodyLarge,
                        color = CastellsTheme.colors.secondaryText,
                    )
                }
            }
            HorizontalDivider()
            Text(
                text = sourceAttribution(item.attribution),
                style = MaterialTheme.typography.bodySmall,
                color = CastellsTheme.colors.secondaryText,
            )
        }
    }
}

private fun sourceAttribution(attribution: String): String {
    val trimmed = attribution.trim()
    return if (trimmed.lowercase().startsWith("font:")) trimmed else "Font: $trimmed"
}
