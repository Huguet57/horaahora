"""The inspection of an app that `make ios-build` built for a profile, and of its build settings."""

from __future__ import annotations

import json
import plistlib
import subprocess
from pathlib import Path
from typing import Any

from scripts.app_profiles.profiles import (
    INTERNAL,
    INTERNAL_SWIFT_MODULES,
    IOS_PROJECT,
    IOS_ROOT,
    PUBLIC,
    SHARED_SWIFT_MODULES,
    Profile,
)


def verify_ios_app(app: Path, profile: Profile) -> list[str]:
    """Problems with a built .app of the profile: its identity and the modules it links."""
    info = plistlib.loads((app / "Info.plist").read_bytes())
    problems = []
    if info.get("CFBundleIdentifier") != profile.ios_bundle_identifier:
        problems.append(f"{app.name}: the bundle identifier is {info.get('CFBundleIdentifier')}")
    if info.get("CFBundleDisplayName") != profile.display_name:
        problems.append(f"{app.name}: the display name is {info.get('CFBundleDisplayName')}")
    if profile is PUBLIC and "remote-notification" in info.get("UIBackgroundModes", []):
        problems.append(f"{app.name}: declares the remote-notification background mode")

    executable = (app / info.get("CFBundleExecutable", app.stem)).read_bytes()
    for module in sorted(SHARED_SWIFT_MODULES - {"CastellsDomain"}):
        if module.encode() not in executable:
            problems.append(f"{app.name}: does not link {module}")
    for module in sorted(INTERNAL_SWIFT_MODULES):
        linked = module.encode() in executable
        if profile is PUBLIC and linked:
            problems.append(f"{app.name}: links {module}")
        if profile is INTERNAL and not linked:
            problems.append(f"{app.name}: does not link {module}")
    return problems


def verify_ios_build_settings(settings: dict[str, Any], profile: Profile) -> list[str]:
    """Problems with the build settings Xcode resolves for the app target of the profile."""
    problems = []
    if settings.get("PRODUCT_BUNDLE_IDENTIFIER") != profile.ios_bundle_identifier:
        problems.append(f"the bundle identifier is {settings.get('PRODUCT_BUNDLE_IDENTIFIER')}")
    entitlements = settings.get("CODE_SIGN_ENTITLEMENTS", "")
    if profile is PUBLIC:
        if entitlements or settings.get("APS_ENVIRONMENT"):
            problems.append("the public app has entitlements for push notifications")
    elif not entitlements:
        problems.append("the internal app has no entitlements")
    else:
        declared = plistlib.loads((IOS_ROOT / entitlements).read_bytes())
        if "aps-environment" not in declared:
            problems.append(f"{entitlements} does not declare aps-environment")
    return problems


def read_ios_build_settings(profile: Profile, configuration: str) -> dict[str, Any]:
    output = subprocess.run(
        [
            "xcodebuild",
            "-showBuildSettings",
            "-json",
            "-project",
            str(IOS_PROJECT),
            "-scheme",
            profile.ios_scheme,
            "-configuration",
            configuration,
            "-destination",
            "generic/platform=iOS",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for entry in json.loads(output):
        if entry.get("target") == profile.ios_scheme:
            return entry["buildSettings"]
    raise ValueError(f"xcodebuild did not report the target {profile.ios_scheme}")


def ios_facts(profile: Profile) -> list[str]:
    """What a successful inspection of the iOS app of the profile has established."""
    return [
        f"bundle identifier {profile.ios_bundle_identifier}, named «{profile.display_name}»",
        f"the executable {'links' if profile is INTERNAL else 'does not link'} "
        + ", ".join(sorted(INTERNAL_SWIFT_MODULES)),
        "the executable links " + ", ".join(sorted(SHARED_SWIFT_MODULES - {"CastellsDomain"})),
        "entitlements for push notifications"
        + (" (aps-environment)" if profile is INTERNAL else ": none"),
    ]
