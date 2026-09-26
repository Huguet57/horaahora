package com.ahuguet.castellsenvena.core.designsystem.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

/** The accent of Castells en vena, shared with the iOS app. */
val BrandRed = Color(0xFFD32B1F)

private val LightColors = lightColorScheme(
    primary = BrandRed,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFFFDAD5),
    onPrimaryContainer = Color(0xFF410001),
    secondary = Color(0xFF6C6C70),
    onSecondary = Color.White,
    background = Color.White,
    onBackground = Color(0xFF111111),
    surface = Color.White,
    onSurface = Color(0xFF111111),
    surfaceVariant = Color(0xFFF2F2F7),
    onSurfaceVariant = Color(0xFF6C6C70),
    surfaceContainerLowest = Color.White,
    surfaceContainerLow = Color(0xFFF7F7FA),
    surfaceContainer = Color(0xFFF2F2F7),
    surfaceContainerHigh = Color(0xFFEBEBF0),
    surfaceContainerHighest = Color(0xFFE5E5EA),
    outline = Color(0xFFC6C6C8),
    outlineVariant = Color(0xFFE5E5EA),
    error = Color(0xFFD70015),
)

private val DarkColors = darkColorScheme(
    primary = BrandRed,
    onPrimary = Color.White,
    primaryContainer = Color(0xFF93000A),
    onPrimaryContainer = Color(0xFFFFDAD5),
    secondary = Color(0xFF98989F),
    onSecondary = Color.Black,
    background = Color.Black,
    onBackground = Color(0xFFF2F2F7),
    surface = Color.Black,
    onSurface = Color(0xFFF2F2F7),
    surfaceVariant = Color(0xFF1C1C1E),
    onSurfaceVariant = Color(0xFF98989F),
    surfaceContainerLowest = Color.Black,
    surfaceContainerLow = Color(0xFF111113),
    surfaceContainer = Color(0xFF1C1C1E),
    surfaceContainerHigh = Color(0xFF2C2C2E),
    surfaceContainerHighest = Color(0xFF3A3A3C),
    outline = Color(0xFF545458),
    outlineVariant = Color(0xFF38383A),
    error = Color(0xFFFF453A),
)

/** Colors the Material scheme has no role for, following the iOS system palette. */
@Immutable
data class CastellsColors(
    /** Behind grouped lists (Ajustos, Hora a Hora). */
    val groupedBackground: Color,
    /** Rows and cards on a grouped background. */
    val groupedCard: Color,
    /** Cards and bubbles on a plain background. */
    val card: Color,
    val secondaryText: Color,
    val tertiaryText: Color,
    val success: Color,
    val warning: Color,
    val star: Color,
)

private val LightCastellsColors = CastellsColors(
    groupedBackground = Color(0xFFF2F2F7),
    groupedCard = Color.White,
    card = Color(0xFFF2F2F5),
    secondaryText = Color(0xFF6C6C70),
    tertiaryText = Color(0xFFAEAEB2),
    success = Color(0xFF248A3D),
    warning = Color(0xFFC93400),
    star = Color(0xFFFFCC00),
)

private val DarkCastellsColors = CastellsColors(
    groupedBackground = Color.Black,
    groupedCard = Color(0xFF1C1C1E),
    card = Color(0xFF1C1C1E),
    secondaryText = Color(0xFF98989F),
    tertiaryText = Color(0xFF636366),
    success = Color(0xFF30D158),
    warning = Color(0xFFFF9F0A),
    star = Color(0xFFFFD60A),
)

private val LocalCastellsColors = staticCompositionLocalOf { LightCastellsColors }

@Composable
fun CastellsTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    CompositionLocalProvider(LocalCastellsColors provides if (darkTheme) DarkCastellsColors else LightCastellsColors) {
        MaterialTheme(
            colorScheme = if (darkTheme) DarkColors else LightColors,
            content = content,
        )
    }
}

object CastellsTheme {
    val colors: CastellsColors
        @Composable
        @ReadOnlyComposable
        get() = LocalCastellsColors.current
}
