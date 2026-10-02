package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.outlined.ContentCopy
import androidx.compose.material.icons.outlined.Email
import androidx.compose.material.icons.outlined.FrontHand
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import com.ahuguet.castellsenvena.core.designsystem.component.ExternalLinkIcon
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionHeader
import com.ahuguet.castellsenvena.core.designsystem.theme.CastellsTheme
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsConfiguration
import kotlinx.coroutines.delay

@Composable
internal fun SettingsRoot(
    configuration: SettingsConfiguration,
    onOpenSources: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onContactSupport: (String) -> Unit,
    onCopyIdentifier: (String) -> Unit,
) {
    SettingsScaffold(title = "Ajustos") {
        SectionHeader("Privacitat i dades")
        ListRow(
            title = "Política de privacitat",
            leadingIcon = Icons.Outlined.FrontHand,
            onClick = { onOpenUrl(configuration.privacyUrl) },
            trailing = { ExternalLinkIcon() },
        )

        SectionHeader("Ajuda")
        ListRow(
            title = "Contacta amb suport",
            leadingIcon = Icons.Outlined.Email,
            onClick = { onContactSupport(configuration.supportEmailUrl) },
            trailing = { ExternalLinkIcon() },
        )
        CopyIdentifierRow(identifier = configuration.technicalIdentifier, onCopy = onCopyIdentifier)

        SectionHeader("Sobre ${configuration.appName}")
        ListRow(
            title = configuration.appName,
            subtitle = configuration.versionAndBuild,
            leadingIcon = Icons.Outlined.Info,
            modifier = Modifier.semantics(mergeDescendants = true) {},
        )
        ListRow(
            title = "Fonts i crèdits",
            leadingIcon = Icons.AutoMirrored.Outlined.MenuBook,
            onClick = onOpenSources,
        )
    }
}

/** Copies the identifier support asks for; confirms it for two seconds. */
@Composable
private fun CopyIdentifierRow(identifier: String, onCopy: (String) -> Unit) {
    var wasCopied by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(wasCopied) {
        if (wasCopied) {
            delay(2_000)
            wasCopied = false
        }
    }
    ListItem(
        headlineContent = { Text(if (wasCopied) "Identificador copiat" else "Copia l'identificador") },
        modifier = Modifier
            .fillMaxWidth()
            .clickable {
                onCopy(identifier)
                wasCopied = true
            }
            .clearAndSetSemantics {
                role = Role.Button
                contentDescription = if (wasCopied) "Identificador tècnic copiat" else "Copia l'identificador tècnic complet"
                stateDescription = identifier
            },
        supportingContent = {
            Text(
                text = identifier,
                style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
                maxLines = 2,
            )
        },
        leadingContent = {
            Icon(
                imageVector = if (wasCopied) Icons.Filled.CheckCircle else Icons.Outlined.ContentCopy,
                contentDescription = null,
                tint = if (wasCopied) CastellsTheme.colors.success else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        },
        colors = ListItemDefaults.colors(containerColor = Color.Transparent),
    )
}
