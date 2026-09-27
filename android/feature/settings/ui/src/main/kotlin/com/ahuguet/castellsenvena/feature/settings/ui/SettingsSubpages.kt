package com.ahuguet.castellsenvena.feature.settings.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.designsystem.component.ExternalLinkIcon
import com.ahuguet.castellsenvena.core.designsystem.component.ListRow
import com.ahuguet.castellsenvena.core.designsystem.component.SectionFooter
import com.ahuguet.castellsenvena.feature.settings.presentation.SettingsCredit

/** Where the data comes from. */
@Composable
internal fun SourcesAndCreditsScreen(
    credits: List<SettingsCredit>,
    onOpenUrl: (String) -> Unit,
    onBack: () -> Unit,
) {
    SettingsScaffold(title = "Fonts i crèdits", onBack = onBack) {
        Spacer(Modifier.height(8.dp))
        for (credit in credits) {
            val url = credit.url
            ListRow(
                title = credit.name,
                subtitle = credit.detail,
                onClick = url?.let { { onOpenUrl(it) } },
                trailing = if (url != null) {
                    { ExternalLinkIcon() }
                } else {
                    null
                },
            )
        }
        SectionFooter(
            "Aquestes atribucions identifiquen les fonts de les dades i no impliquen cap col·laboració formal.",
        )
    }
}

/**
 * A settings page under a top app bar, with a back arrow on the subpages.
 * Scrolls as a whole, with room at the end.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScaffold(
    title: String,
    onBack: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()
    val navigationIcon: @Composable () -> Unit = {
        if (onBack != null) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Enrere")
            }
        }
    }
    Scaffold(
        modifier = Modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            TopAppBar(title = { Text(title) }, navigationIcon = navigationIcon, scrollBehavior = scrollBehavior)
        },
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(PaddingValues(bottom = 32.dp)),
            content = content,
        )
    }
}
