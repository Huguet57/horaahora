"""The public app keeps the calculator, the score table and their settings, and nothing else.

Hora a Hora, Agenda, their settings, the secret gesture and the news notifications live only in
the internal app, a separate development app. These tests read the Xcode project, the Swift
package and the Gradle build, and fail if an internal module, entry point, permission or
entitlement reaches the public app, or if the internal app could take the public app's place.
"""

from __future__ import annotations

import os
import plistlib
import re
import subprocess
from pathlib import Path

import pytest

from scripts.app_profiles.gradle_build import (
    android_variant_libraries,
    android_variant_projects,
    gradle_project_dependencies,
    gradle_projects,
    kotlin_imports,
)
from scripts.app_profiles.profiles import (
    ANDROID_ROOT,
    INTERNAL,
    INTERNAL_GRADLE_PROJECTS,
    INTERNAL_KOTLIN_PACKAGES,
    INTERNAL_SWIFT_MODULES,
    IOS_ROOT,
    PUBLIC,
    REPOSITORY_ROOT,
    SHARED_SWIFT_MODULES,
    in_packages,
)
from scripts.app_profiles.swift_package import swift_imports, swift_package
from scripts.app_profiles.xcode_project import xcode_scheme, xcode_targets

SWIFT_SOURCES = IOS_ROOT / "Packages" / "CastellsKit" / "Sources"
APP = ANDROID_ROOT / "app"
PRODUCTION_API = "https://castells-superapp-poc.vercel.app"

# What the public app must never call or build: the ways back to the internal sections and
# to news notifications (permission, registration, presentation and the secret gesture).
IOS_INTERNAL_ENTRY_POINTS = (
    r"(?<!un)registerForRemoteNotifications",
    r"requestAuthorization",
    r"UNUserNotificationCenterDelegate",
    r"UIApplicationDelegateAdaptor",
    r"PushSubscriptionCoordinator",
    r"NotificationPreferenceStore",
    r"HiddenSections",
    r"SecretTap",
    r"HourByHourNotification",
)
ANDROID_INTERNAL_ENTRY_POINTS = (
    r"POST_NOTIFICATIONS",
    r"FirebaseMessaging",
    r"PushSubscriptionCoordinator",
    r"NotificationPreferenceStore",
    r"HiddenSections",
    r"SecretTap",
    r"HourByHourNotification",
    r"createNotificationChannel",
    r"NotificationCompat",
)


def matches(source: Path, patterns: tuple[str, ...]) -> list[str]:
    text = source.read_text()
    return [pattern for pattern in patterns if re.search(pattern, text)]


def kotlin_sources(*folders: Path) -> list[Path]:
    return sorted(source for folder in folders for source in folder.rglob("*.kt"))


# --- iOS ---------------------------------------------------------------------------------------


def test_ios_public_app_links_only_the_shared_modules() -> None:
    public = xcode_targets()[PUBLIC.ios_scheme]

    assert public.products == SHARED_SWIFT_MODULES
    assert public.linked_products == SHARED_SWIFT_MODULES


def test_ios_internal_app_adds_the_internal_modules() -> None:
    internal = xcode_targets()[INTERNAL.ios_scheme]

    assert internal.products == SHARED_SWIFT_MODULES | INTERNAL_SWIFT_MODULES
    assert internal.linked_products == internal.products


def test_ios_shared_modules_do_not_depend_on_internal_ones() -> None:
    package = swift_package()

    assert SHARED_SWIFT_MODULES | INTERNAL_SWIFT_MODULES <= set(package.products)
    assert package.closure(SHARED_SWIFT_MODULES).isdisjoint(INTERNAL_SWIFT_MODULES)
    for module in SHARED_SWIFT_MODULES:
        for source in (SWIFT_SOURCES / module).rglob("*.swift"):
            assert swift_imports(source).isdisjoint(INTERNAL_SWIFT_MODULES), source


def test_ios_shared_features_have_no_internal_entry_points() -> None:
    # The data layer keeps the news and Agenda code, which the internal app still needs and
    # which the public app never reaches; the features it shares must not offer them.
    for module in SHARED_SWIFT_MODULES - {"CastellsDomain", "CastellsData"}:
        for source in (SWIFT_SOURCES / module).rglob("*.swift"):
            assert matches(source, IOS_INTERNAL_ENTRY_POINTS) == [], source


def test_ios_public_app_sources_have_no_internal_entry_points() -> None:
    targets = xcode_targets()
    public = targets[PUBLIC.ios_scheme]
    internal = targets[INTERNAL.ios_scheme]

    assert public.sources
    for path in public.sources:
        source = IOS_ROOT / path
        assert swift_imports(source).isdisjoint(INTERNAL_SWIFT_MODULES), path
        assert matches(source, IOS_INTERNAL_ENTRY_POINTS) == [], path
    assert not [path for path in public.sources if path.startswith("HoraAHoraApp/Internal/")]
    assert not [path for path in internal.sources if path.startswith("HoraAHoraApp/Public/")]


def test_ios_public_app_keeps_its_identity_and_the_internal_one_cannot_replace_it() -> None:
    targets = xcode_targets()
    icons = IOS_ROOT / "HoraAHoraApp" / "Assets.xcassets"

    for configuration in ("Debug", "Release"):
        public = targets[PUBLIC.ios_scheme].configurations[configuration]
        internal = targets[INTERNAL.ios_scheme].configurations[configuration]
        assert public["PRODUCT_BUNDLE_IDENTIFIER"] == PUBLIC.ios_bundle_identifier
        assert internal["PRODUCT_BUNDLE_IDENTIFIER"] == INTERNAL.ios_bundle_identifier
        assert public["INFOPLIST_KEY_CFBundleDisplayName"] == PUBLIC.display_name
        assert internal["INFOPLIST_KEY_CFBundleDisplayName"] == INTERNAL.display_name
        assert public["ASSETCATALOG_COMPILER_APPICON_NAME"] == "AppIcon"
        assert internal["ASSETCATALOG_COMPILER_APPICON_NAME"] == "AppIconInternal"
    assert (icons / "AppIcon.appiconset" / "AppIcon.png").is_file()
    assert (icons / "AppIconInternal.appiconset" / "AppIconInternal.png").is_file()


def test_ios_only_the_internal_app_can_receive_push_notifications() -> None:
    targets = xcode_targets()

    for configuration, environment in (("Debug", "development"), ("Release", "production")):
        public = targets[PUBLIC.ios_scheme].configurations[configuration]
        internal = targets[INTERNAL.ios_scheme].configurations[configuration]
        assert "CODE_SIGN_ENTITLEMENTS" not in public
        assert "APS_ENVIRONMENT" not in public
        assert internal["APS_ENVIRONMENT"] == environment
        entitlements = IOS_ROOT / internal["CODE_SIGN_ENTITLEMENTS"]
        assert plistlib.loads(entitlements.read_bytes()) == {
            "aps-environment": "$(APS_ENVIRONMENT)"
        }
    assert not (IOS_ROOT / "HoraAHoraApp" / "HoraAHoraApp.entitlements").exists()


def test_ios_internal_app_uses_the_same_backends_as_the_public_one() -> None:
    targets = xcode_targets()

    for target in (targets[PUBLIC.ios_scheme], targets[INTERNAL.ios_scheme]):
        assert target.configurations["Release"]["CASTELLS_API_BASE_URL"] == PRODUCTION_API
        assert "CASTELLS_API_BASE_URL" not in target.configurations["Debug"]
        assert target.base_configurations == {
            "Debug": "HoraAHoraApp/Configuration/Debug.xcconfig",
            "Release": None,
        }


def test_ios_schemes_build_and_archive_one_profile_each() -> None:
    for profile in (PUBLIC, INTERNAL):
        assert xcode_scheme(profile.ios_scheme) == {
            "targets": [profile.ios_scheme],
            "archive_configuration": "Release",
        }


# --- Android -----------------------------------------------------------------------------------


def test_android_public_app_cannot_reach_the_internal_modules() -> None:
    public = android_variant_projects("public")

    assert public.isdisjoint(INTERNAL_GRADLE_PROJECTS)
    assert {":feature:calculator:ui", ":feature:scoretable:ui", ":feature:settings:ui"} <= public


def test_android_internal_app_adds_the_internal_modules() -> None:
    assert INTERNAL_GRADLE_PROJECTS <= gradle_projects()
    assert INTERNAL_GRADLE_PROJECTS <= android_variant_projects("internal")


def test_android_shared_modules_do_not_depend_on_internal_ones() -> None:
    for project in gradle_projects() - INTERNAL_GRADLE_PROJECTS - {":app"}:
        for dependencies in gradle_project_dependencies(project).values():
            assert dependencies.isdisjoint(INTERNAL_GRADLE_PROJECTS), project


def test_android_firebase_is_only_in_the_internal_app() -> None:
    public = android_variant_libraries("public")
    internal = android_variant_libraries("internal")
    conventions = (ANDROID_ROOT / "build-logic").rglob("*.kt")

    assert not [alias for alias in public if alias.startswith("firebase")]
    assert {"firebase.bom", "firebase.messaging"} <= internal
    assert not [path for path in conventions if "google-services" in path.read_text()]


def test_android_public_app_sources_have_no_internal_code() -> None:
    shared_modules = [
        ANDROID_ROOT.joinpath(*project.strip(":").split(":"), "src", "main")
        for project in gradle_projects() - INTERNAL_GRADLE_PROJECTS - {":app"}
    ]
    public_app = kotlin_sources(APP / "src" / "main", APP / "src" / "public")

    assert public_app
    for source in kotlin_sources(*shared_modules) + public_app:
        imports = kotlin_imports(source)
        assert not [name for name in imports if in_packages(name, INTERNAL_KOTLIN_PACKAGES)], source
    for source in public_app:
        package = re.search(r"^package ([\w.]+)", source.read_text(), re.M)
        assert package is not None and not in_packages(package[1], INTERNAL_KOTLIN_PACKAGES)
        assert matches(source, ANDROID_INTERNAL_ENTRY_POINTS) == [], source


def test_android_only_the_internal_manifest_declares_news_notifications() -> None:
    main = (APP / "src" / "main" / "AndroidManifest.xml").read_text()
    public = APP / "src" / "public" / "AndroidManifest.xml"
    internal = (APP / "src" / "internal" / "AndroidManifest.xml").read_text()

    for manifest in (main, public.read_text() if public.exists() else ""):
        assert "POST_NOTIFICATIONS" not in manifest
        assert "MESSAGING_EVENT" not in manifest
        assert "firebase" not in manifest
    assert "android.permission.POST_NOTIFICATIONS" in internal
    assert ".notifications.CastellsMessagingService" in internal
    assert "com.google.firebase.MESSAGING_EVENT" in internal
    assert "firebase_messaging_auto_init_enabled" in internal


def test_android_public_app_keeps_its_identity_and_the_internal_one_cannot_replace_it() -> None:
    build = (APP / "build.gradle.kts").read_text()
    flavors = re.search(r"productFlavors \{\n(.*?)\n    \}\n", build, flags=re.S)
    main_strings = (APP / "src" / "main" / "res" / "values" / "strings.xml").read_text()
    internal_strings = (APP / "src" / "internal" / "res" / "values" / "strings.xml").read_text()
    main_colors = (APP / "src" / "main" / "res" / "values" / "colors.xml").read_text()
    internal_colors = (APP / "src" / "internal" / "res" / "values" / "colors.xml").read_text()

    assert f'applicationId = "{PUBLIC.android_application_id}"' in build
    assert flavors is not None
    public_flavor, internal_flavor = re.findall(
        r'create\("(?:public|internal)"\) \{\n(.*?)\n        \}', flavors[1], flags=re.S
    )
    assert "applicationId" not in public_flavor
    suffix = INTERNAL.android_application_id.removeprefix(PUBLIC.android_application_id)
    assert f'applicationIdSuffix = "{suffix}"' in internal_flavor
    assert '<string name="app_name">La calculadora de l\\\'Aleta</string>' in main_strings
    assert f'<string name="app_name">{INTERNAL.display_name}</string>' in internal_strings
    launcher_background = r'<color name="ic_launcher_background">(#\w+)</color>'
    assert re.findall(launcher_background, main_colors) != re.findall(
        launcher_background, internal_colors
    )


def test_android_builds_only_the_selected_profile_and_public_by_default() -> None:
    build = (APP / "build.gradle.kts").read_text()

    assert 'providers.gradleProperty("castells.buildProfile")' in build
    assert 'providers.environmentVariable("CASTELLS_BUILD_PROFILE")' in build
    assert '.getOrElse("public")' in build
    assert "variant.enable = variant.flavorName == buildProfile" in build


# --- Build commands ----------------------------------------------------------------------------


def make_dry_run(*arguments: str, profile: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = {k: v for k, v in os.environ.items() if k != "CASTELLS_BUILD_PROFILE"}
    if profile is not None:
        environment["CASTELLS_BUILD_PROFILE"] = profile
    return subprocess.run(
        ["make", "-n", *arguments],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_make_builds_the_public_apps_by_default() -> None:
    ios = make_dry_run("ios-build", "ios-verify")
    android = make_dry_run("android-build", "android-verify", "android-install")

    assert ios.returncode == 0, ios.stderr
    assert "-scheme HoraAHoraApp " in ios.stdout
    assert "HoraAHoraAppInternal" not in ios.stdout
    assert "python3 -m scripts.app_profiles ios public" in ios.stdout
    assert android.returncode == 0, android.stderr
    assert "-Pcastells.buildProfile=public" in android.stdout
    assert ":app:installPublicDebug" in android.stdout
    assert "python3 -m scripts.app_profiles android public" in android.stdout


@pytest.mark.parametrize("from_environment", [True, False])
def test_make_builds_the_internal_apps_when_asked(from_environment: bool) -> None:
    variable = [] if from_environment else ["CASTELLS_BUILD_PROFILE=internal"]
    profile = "internal" if from_environment else None
    ios = make_dry_run("ios-build", *variable, profile=profile)
    android = make_dry_run("android-build", "android-install", *variable, profile=profile)

    assert ios.returncode == 0, ios.stderr
    assert "-scheme HoraAHoraAppInternal " in ios.stdout
    assert android.returncode == 0, android.stderr
    assert "-Pcastells.buildProfile=internal" in android.stdout
    assert ":app:installInternalDebug" in android.stdout


def test_make_rejects_an_unknown_profile() -> None:
    result = make_dry_run("ios-build", profile="beta")

    assert result.returncode != 0
    assert "CASTELLS_BUILD_PROFILE must be public or internal" in result.stderr
