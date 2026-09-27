package com.ahuguet.castellsenvena.core.designsystem.theme

import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight

/**
 * Whether the user turned animations off in the system accessibility settings.
 * The app provides it; screens then switch states without animating.
 */
val LocalReduceMotion = staticCompositionLocalOf { false }

/** Digits of equal width, for times and scores that line up. */
val TabularNumbers = TextStyle(fontFeatureSettings = "tnum")

/** Castell notation such as 4de10fm. */
val CastellNotation = TextStyle(fontFamily = FontFamily.Monospace, fontWeight = FontWeight.SemiBold)
