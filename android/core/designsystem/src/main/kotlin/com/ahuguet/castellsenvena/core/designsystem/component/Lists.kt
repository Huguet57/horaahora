package com.ahuguet.castellsenvena.core.designsystem.component

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowOutward
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

/*
 * Lists as Android draws them: rows straight on the surface, and sections
 * that start with a header in the accent color, like the system settings.
 */

@Composable
fun SectionHeader(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleSmall,
        color = MaterialTheme.colorScheme.primary,
        modifier = modifier
            .fillMaxWidth()
            .padding(start = 16.dp, end = 16.dp, top = 20.dp, bottom = 4.dp)
            .semantics { heading() },
    )
}

@Composable
fun SectionFooter(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = modifier
            .fillMaxWidth()
            .padding(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 8.dp),
    )
}

/** A Material list item over the surface it lies on. */
@Composable
fun ListRow(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    leadingIcon: ImageVector? = null,
    leadingIconTint: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    titleColor: Color = MaterialTheme.colorScheme.onSurface,
    enabled: Boolean = true,
    onClickLabel: String? = null,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    val clickable = if (onClick != null) {
        Modifier.clickable(enabled = enabled, onClickLabel = onClickLabel, onClick = onClick)
    } else {
        Modifier
    }
    ListItem(
        headlineContent = { Text(text = title, color = titleColor) },
        modifier = modifier
            .fillMaxWidth()
            .then(clickable)
            .alpha(if (enabled) 1f else 0.38f),
        supportingContent = subtitle?.let { { Text(text = it) } },
        leadingContent = leadingIcon?.let { icon -> { Icon(imageVector = icon, contentDescription = null, tint = leadingIconTint) } },
        trailingContent = trailing,
        colors = ListItemDefaults.colors(containerColor = Color.Transparent),
    )
}

/** Marks a row that leaves the app. */
@Composable
fun ExternalLinkIcon(modifier: Modifier = Modifier) {
    Icon(
        imageVector = Icons.Filled.ArrowOutward,
        contentDescription = null,
        tint = MaterialTheme.colorScheme.outline,
        modifier = modifier.size(16.dp),
    )
}
