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

/*
 * Material 3 schemes generated from BrandRed with Material Color Utilities:
 * the brand's tonal palette for the accents and near-neutral surfaces
 * (chroma 3, and 5 for the variants), so the app stays red on white instead
 * of turning pink. The light scheme keeps BrandRed itself as its primary.
 */
private val LightColors = lightColorScheme(
    primary = BrandRed,
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFFFDAD5),
    onPrimaryContainer = Color(0xFF930002),
    inversePrimary = Color(0xFFFFB4A9),
    secondary = Color(0xFF775651),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFFFDAD5),
    onSecondaryContainer = Color(0xFF5D3F3B),
    tertiary = Color(0xFF705C2E),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFFCDFA6),
    onTertiaryContainer = Color(0xFF574419),
    background = Color(0xFFFFF8F6),
    onBackground = Color(0xFF1F1A1A),
    surface = Color(0xFFFFF8F6),
    onSurface = Color(0xFF1F1A1A),
    surfaceVariant = Color(0xFFEFDFDD),
    onSurfaceVariant = Color(0xFF4F4443),
    surfaceTint = BrandRed,
    inverseSurface = Color(0xFF352F2E),
    inverseOnSurface = Color(0xFFF9EEED),
    error = Color(0xFFBA1A1A),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF93000A),
    outline = Color(0xFF807473),
    outlineVariant = Color(0xFFD2C3C1),
    scrim = Color(0xFF000000),
    surfaceBright = Color(0xFFFFF8F6),
    surfaceDim = Color(0xFFE2D8D6),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFFCF1EF),
    surfaceContainer = Color(0xFFF6EBEA),
    surfaceContainerHigh = Color(0xFFF1E6E4),
    surfaceContainerHighest = Color(0xFFEBE0DE),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFFFB4A9),
    onPrimary = Color(0xFF690001),
    primaryContainer = Color(0xFF930002),
    onPrimaryContainer = Color(0xFFFFDAD5),
    inversePrimary = Color(0xFFBB1710),
    secondary = Color(0xFFE7BDB6),
    onSecondary = Color(0xFF442925),
    secondaryContainer = Color(0xFF5D3F3B),
    onSecondaryContainer = Color(0xFFFFDAD5),
    tertiary = Color(0xFFDEC38C),
    onTertiary = Color(0xFF3E2E04),
    tertiaryContainer = Color(0xFF574419),
    onTertiaryContainer = Color(0xFFFCDFA6),
    background = Color(0xFF171212),
    onBackground = Color(0xFFEBE0DE),
    surface = Color(0xFF171212),
    onSurface = Color(0xFFEBE0DE),
    surfaceVariant = Color(0xFF4F4443),
    onSurfaceVariant = Color(0xFFD2C3C1),
    surfaceTint = Color(0xFFFFB4A9),
    inverseSurface = Color(0xFFEBE0DE),
    inverseOnSurface = Color(0xFF352F2E),
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    outline = Color(0xFF9B8E8C),
    outlineVariant = Color(0xFF4F4443),
    scrim = Color(0xFF000000),
    surfaceBright = Color(0xFF3E3837),
    surfaceDim = Color(0xFF171212),
    surfaceContainerLowest = Color(0xFF110D0D),
    surfaceContainerLow = Color(0xFF1F1A1A),
    surfaceContainer = Color(0xFF231E1E),
    surfaceContainerHigh = Color(0xFF2E2928),
    surfaceContainerHighest = Color(0xFF393333),
)

/** Colors the Material scheme has no role for. */
@Immutable
data class CastellsColors(
    /** Harmonized with BrandRed, like the Material custom colors. */
    val success: Color,
    /** Harmonized with BrandRed, like the Material custom colors. */
    val warning: Color,
    /** Featured groups and winning results, in the gold of starred items on Android. */
    val star: Color,
)

private val LightCastellsColors = CastellsColors(
    success = Color(0xFF386A00),
    warning = Color(0xFFA83901),
    star = Color(0xFFF4B400),
)

private val DarkCastellsColors = CastellsColors(
    success = Color(0xFF9AD863),
    warning = Color(0xFFFFB59A),
    star = Color(0xFFFDD663),
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
