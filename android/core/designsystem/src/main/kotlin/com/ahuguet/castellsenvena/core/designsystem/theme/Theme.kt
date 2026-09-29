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

/** The accent of La calculadora de l'Aleta, shared with the iOS app. */
val BrandRed = Color(0xFFD32B1F)

/*
 * Brand colors are reserved for accents and semantic states. Surface, text and
 * outline roles use neutral grays in both modes; transparent surface tint keeps
 * elevated Material components from picking up a red cast.
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
    background = Color(0xFFFFFFFF),
    onBackground = Color(0xFF1B1B1B),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF1B1B1B),
    surfaceVariant = Color(0xFFE3E3E3),
    onSurfaceVariant = Color(0xFF474747),
    surfaceTint = Color.Transparent,
    inverseSurface = Color(0xFF303030),
    inverseOnSurface = Color(0xFFF2F2F2),
    error = Color(0xFFBA1A1A),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF93000A),
    outline = Color(0xFF757575),
    outlineVariant = Color(0xFFC7C7C7),
    scrim = Color(0xFF000000),
    surfaceBright = Color(0xFFFFFFFF),
    surfaceDim = Color(0xFFDADADA),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFF7F7F7),
    surfaceContainer = Color(0xFFF0F0F0),
    surfaceContainerHigh = Color(0xFFE8E8E8),
    surfaceContainerHighest = Color(0xFFE2E2E2),
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
    background = Color(0xFF121212),
    onBackground = Color(0xFFE5E5E5),
    surface = Color(0xFF121212),
    onSurface = Color(0xFFE5E5E5),
    surfaceVariant = Color(0xFF474747),
    onSurfaceVariant = Color(0xFFC7C7C7),
    surfaceTint = Color.Transparent,
    inverseSurface = Color(0xFFE5E5E5),
    inverseOnSurface = Color(0xFF303030),
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    outline = Color(0xFF919191),
    outlineVariant = Color(0xFF474747),
    scrim = Color(0xFF000000),
    surfaceBright = Color(0xFF383838),
    surfaceDim = Color(0xFF121212),
    surfaceContainerLowest = Color(0xFF0D0D0D),
    surfaceContainerLow = Color(0xFF1A1A1A),
    surfaceContainer = Color(0xFF1F1F1F),
    surfaceContainerHigh = Color(0xFF292929),
    surfaceContainerHighest = Color(0xFF333333),
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
