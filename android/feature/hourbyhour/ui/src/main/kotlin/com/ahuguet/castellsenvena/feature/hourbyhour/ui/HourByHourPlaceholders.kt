package com.ahuguet.castellsenvena.feature.hourbyhour.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.SkeletonBlock
import com.ahuguet.castellsenvena.core.designsystem.component.rememberPulseAlpha

/** Placeholder rows while the first page loads. */
@Composable
internal fun HourByHourSkeleton() {
    val alpha = rememberPulseAlpha()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .alpha(alpha)
            .clearAndSetSemantics { contentDescription = "Carregant l'Hora a Hora" },
    ) {
        repeat(2) { section ->
            SkeletonBlock(
                width = 190.dp,
                height = 14.dp,
                modifier = Modifier.padding(start = 16.dp, top = 24.dp, bottom = 8.dp),
            )
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(PaddingValues(horizontal = 16.dp, vertical = 12.dp)),
                verticalArrangement = Arrangement.spacedBy(24.dp),
            ) {
                repeat(3) { row -> SkeletonRow(showsSecondSummaryLine = (section + row) % 2 == 0) }
            }
        }
    }
}

@Composable
private fun SkeletonRow(showsSecondSummaryLine: Boolean) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SkeletonBlock(width = 36.dp, height = 11.dp)
            Spacer(Modifier.weight(1f))
            SkeletonBlock(width = 96.dp, height = 10.dp)
        }
        SkeletonBlock(width = 260.dp, height = 16.dp)
        SkeletonBlock(width = 300.dp, height = 12.dp)
        if (showsSecondSummaryLine) SkeletonBlock(width = 200.dp, height = 12.dp)
    }
}

/** Offers the news notifications without asking for the permission at launch. */
@Composable
internal fun NotificationOnboardingCard(
    onConfigure: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceContainerHighest,
    ) {
        Row(
            modifier = Modifier.padding(start = 14.dp, top = 14.dp, bottom = 6.dp),
            verticalAlignment = Alignment.Top,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Icon(
                imageVector = Icons.Filled.NotificationsActive,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(28.dp),
            )
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(
                    text = "Vols rebre les novetats?",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                Text(
                    text = "Activa els avisos de l'Hora a Hora quan tu vulguis.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                TextButton(onClick = onConfigure, contentPadding = PaddingValues(0.dp)) {
                    Text("Configura-ho", fontWeight = FontWeight.SemiBold)
                }
            }
            IconButton(onClick = onDismiss) {
                Icon(
                    imageVector = Icons.Filled.Close,
                    contentDescription = "Ara no",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
