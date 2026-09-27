package com.ahuguet.castellsenvena.feature.calculator.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ahuguet.castellsenvena.core.common.CatalanNumbers
import com.ahuguet.castellsenvena.core.designsystem.theme.TabularNumbers
import com.ahuguet.castellsenvena.core.domain.chat.ChatMessage
import com.ahuguet.castellsenvena.core.domain.chat.ChatRole
import com.ahuguet.castellsenvena.core.domain.chat.MessageDeliveryState
import com.ahuguet.castellsenvena.feature.calculator.presentation.CalculationPresentation
import com.ahuguet.castellsenvena.feature.calculator.ui.answer.ComparisonTable
import com.ahuguet.castellsenvena.feature.calculator.ui.answer.PerformanceSummary
import com.ahuguet.castellsenvena.feature.calculator.ui.answer.ScoreRanking

/** Space kept on the far side of a bubble, so both speakers stay apart. */
private val BubbleInset = 44.dp

@Composable
internal fun MessageBubble(message: ChatMessage, onRetry: () -> Unit, modifier: Modifier = Modifier) {
    val isUser = message.role == ChatRole.USER
    Row(modifier = modifier.fillMaxWidth(), horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start) {
        if (isUser) Spacer(Modifier.width(BubbleInset))
        Surface(
            modifier = Modifier.weight(1f, fill = false),
            shape = RoundedCornerShape(16.dp),
            color = if (isUser) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceContainerHigh,
            contentColor = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface,
        ) {
            Column(modifier = Modifier.padding(11.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                val presentation = remember(message.calculation) { CalculationPresentation.from(message.calculation) }
                when (presentation) {
                    is CalculationPresentation.Comparison -> {
                        SelectionContainer { Text(presentation.presentation.summary) }
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        ComparisonTable(presentation.presentation)
                    }
                    is CalculationPresentation.Ranking -> ScoreRanking(presentation.presentation)
                    is CalculationPresentation.Summary -> PerformanceSummary(presentation.presentation)
                    null -> ProseAnswer(message)
                }
                if (message.deliveryState == MessageDeliveryState.FAILED) {
                    TextButton(onClick = onRetry, contentPadding = PaddingValues(horizontal = 8.dp)) {
                        Text("Torna-ho a provar", color = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
        if (!isUser) Spacer(Modifier.width(BubbleInset))
    }
}

/** The text of a message, and the totals of an answer without a table. */
@Composable
private fun ProseAnswer(message: ChatMessage) {
    SelectionContainer { Text(message.content) }
    val performances = message.calculation?.performances.orEmpty()
    if (performances.isNotEmpty()) {
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        for (performance in performances) {
            Row {
                Text(
                    text = performance.label,
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    text = CatalanNumbers.grouped(performance.total),
                    style = MaterialTheme.typography.bodySmall.merge(TabularNumbers),
                )
            }
        }
    }
}
