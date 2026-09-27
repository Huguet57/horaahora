"""The two build profiles, where the apps live and what only the internal app may contain."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IOS_ROOT = REPOSITORY_ROOT / "HoraAHoraApp"
IOS_PROJECT = IOS_ROOT / "HoraAHoraApp.xcodeproj"
SWIFT_PACKAGE = IOS_ROOT / "Packages" / "CastellsKit" / "Package.swift"
ANDROID_ROOT = REPOSITORY_ROOT / "android"


@dataclass(frozen=True)
class Profile:
    name: str
    ios_scheme: str
    ios_bundle_identifier: str
    display_name: str
    android_application_id: str


PUBLIC = Profile(
    name="public",
    ios_scheme="HoraAHoraApp",
    ios_bundle_identifier="com.ahuguet.castellsenvena",
    display_name="La calculadora de l'Aleta",
    android_application_id="com.ahuguet.castellsenvena",
)
INTERNAL = Profile(
    name="internal",
    ios_scheme="HoraAHoraAppInternal",
    ios_bundle_identifier="com.ahuguet.castellsenvena.internal",
    display_name="Aleta interna",
    android_application_id="com.ahuguet.castellsenvena.internal",
)
PROFILES = {profile.name: profile for profile in (PUBLIC, INTERNAL)}

# The Swift modules both apps share, and the ones only the internal app links.
SHARED_SWIFT_MODULES = frozenset(
    {"CastellsDomain", "CastellsData", "FeatureCalculator", "FeatureScoreTable", "FeatureSettings"}
)
INTERNAL_SWIFT_MODULES = frozenset(
    {"CastellsInternalData", "FeatureHourByHour", "FeatureAgenda", "FeatureInternalSettings"}
)

# The Gradle projects only the internal app depends on.
INTERNAL_GRADLE_PROJECTS = frozenset(
    {
        ":core:internaldata",
        ":feature:hourbyhour:presentation",
        ":feature:hourbyhour:ui",
        ":feature:agenda:presentation",
        ":feature:agenda:ui",
        ":feature:internalsettings:presentation",
        ":feature:internalsettings:ui",
    }
)
SHARED_KOTLIN_PACKAGES = (
    "com.ahuguet.castellsenvena.feature.calculator",
    "com.ahuguet.castellsenvena.feature.scoretable",
    "com.ahuguet.castellsenvena.feature.settings",
)
# The code of the internal sections, of their data, of the news notifications and of Firebase.
INTERNAL_KOTLIN_PACKAGES = (
    "com.ahuguet.castellsenvena.core.internaldata",
    "com.ahuguet.castellsenvena.feature.hourbyhour",
    "com.ahuguet.castellsenvena.feature.agenda",
    "com.ahuguet.castellsenvena.feature.internalsettings",
    "com.ahuguet.castellsenvena.notifications",
    "com.google.firebase",
)
# What only the internal app's merged manifest declares.
INTERNAL_MANIFEST_ENTRIES = (
    "android.permission.POST_NOTIFICATIONS",
    "com.ahuguet.castellsenvena.notifications.CastellsMessagingService",
    "com.google.firebase",
)


def in_packages(name: str, packages: Iterable[str]) -> bool:
    """Whether a dotted name belongs to one of the packages, or is one of them."""
    return any(name == package or name.startswith(package + ".") for package in packages)
