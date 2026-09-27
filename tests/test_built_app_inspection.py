"""The inspection CI runs on the built apps, with small fakes of APKs, apps and xcodebuild.

After building each profile, `make android-verify` and `make ios-verify` run
`python3 -m scripts.app_profiles`, which fails if an internal module, permission or entitlement
reached the public app, or if the internal app lost what only it has.
"""

from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.app_profiles.android_inspection import verify_android_apk, verify_android_mapping
from scripts.app_profiles.ios_inspection import verify_ios_app, verify_ios_build_settings
from scripts.app_profiles.profiles import (
    INTERNAL,
    INTERNAL_KOTLIN_PACKAGES,
    PUBLIC,
    REPOSITORY_ROOT,
    SHARED_SWIFT_MODULES,
)
from scripts.app_profiles.xcode_project import xcode_targets

PUBLIC_PACKAGES = [
    "com.ahuguet.castellsenvena.feature.calculator.ui",
    "com.ahuguet.castellsenvena.feature.scoretable.ui",
    "com.ahuguet.castellsenvena.feature.settings.ui",
]


def fake_apk(folder: Path, manifest: list[str], packages: list[str]) -> Path:
    """An APK with the given manifest strings, in UTF-16 as in binary XML, and classes."""
    apk = folder / "app.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr(
            "AndroidManifest.xml",
            b"\x03\x00\x08\x00" + b"".join(text.encode("utf-16-le") + b"\0\0" for text in manifest),
        )
        descriptors = [f"L{package.replace('.', '/')}/Screen;" for package in packages]
        archive.writestr("classes.dex", b"dex\n035\0" + "\0".join(descriptors).encode())
    return apk


def fake_android_outputs(folder: Path, packages: list[str]) -> Path:
    """What `make android-build` leaves for the public app: two APKs and the R8 mapping."""
    outputs = folder / "outputs"
    for build_type in ("debug", "release"):
        apks = outputs / "apk" / "public" / build_type
        apks.mkdir(parents=True)
        fake_apk(apks, [PUBLIC.android_application_id], packages)
    mapping = outputs / "mapping" / "publicRelease" / "mapping.txt"
    mapping.parent.mkdir(parents=True)
    mapping.write_text("# compiler: R8\n")
    return outputs


def fake_ios_app(folder: Path, profile_bundle: str, name: str, modules: list[str]) -> Path:
    app = folder / "App.app"
    app.mkdir()
    info = {
        "CFBundleIdentifier": profile_bundle,
        "CFBundleDisplayName": name,
        "CFBundleExecutable": "App",
    }
    (app / "Info.plist").write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY))
    (app / "App").write_bytes(b"\xcf\xfa\xed\xfe" + b"\0".join(m.encode() for m in modules))
    return app


def fake_xcodebuild(folder: Path, settings: dict[str, str]) -> Path:
    """A folder with an xcodebuild that reports the public app's build settings.

    It writes the arguments it received, one per line, to xcodebuild.arguments.
    """
    tools = folder / "bin"
    tools.mkdir()
    report = json.dumps([{"target": PUBLIC.ios_scheme, "buildSettings": settings}])
    xcodebuild = tools / "xcodebuild"
    xcodebuild.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$0.arguments\"\ncat <<'EOF'\n{report}\nEOF\n"
    )
    xcodebuild.chmod(0o755)
    return tools


def run_inspection(*arguments: str, tools: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if tools is not None:
        environment["PATH"] = f"{tools}{os.pathsep}{environment['PATH']}"
    return subprocess.run(
        [sys.executable, "-m", "scripts.app_profiles", *arguments],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


# --- Android -----------------------------------------------------------------------------------


def test_apk_inspection_accepts_the_public_app_and_rejects_internal_code(tmp_path: Path) -> None:
    clean = fake_apk(tmp_path, ["com.ahuguet.castellsenvena"], PUBLIC_PACKAGES)
    assert verify_android_apk(clean, PUBLIC, minified=False) == []

    leaking = fake_apk(
        tmp_path,
        ["com.ahuguet.castellsenvena", "android.permission.POST_NOTIFICATIONS"],
        [*PUBLIC_PACKAGES, "com.ahuguet.castellsenvena.feature.agenda.ui", "com.google.firebase"],
    )
    assert verify_android_apk(leaking, PUBLIC, minified=False) == [
        "app.apk: the manifest declares android.permission.POST_NOTIFICATIONS",
        "app.apk: contains classes of com.ahuguet.castellsenvena.feature.agenda",
        "app.apk: contains classes of com.google.firebase",
    ]


def test_apk_inspection_requires_the_internal_sections_in_the_internal_app(
    tmp_path: Path,
) -> None:
    manifest = [
        "com.ahuguet.castellsenvena.internal",
        "android.permission.POST_NOTIFICATIONS",
        "com.ahuguet.castellsenvena.notifications.CastellsMessagingService",
    ]
    complete = fake_apk(tmp_path, manifest, [*PUBLIC_PACKAGES, *INTERNAL_KOTLIN_PACKAGES])
    assert verify_android_apk(complete, INTERNAL, minified=False) == []

    public_only = fake_apk(tmp_path, ["com.ahuguet.castellsenvena"], PUBLIC_PACKAGES)
    problems = verify_android_apk(public_only, INTERNAL, minified=False)
    assert "app.apk: the manifest is not com.ahuguet.castellsenvena.internal" in problems
    assert "app.apk: no classes of com.ahuguet.castellsenvena.feature.hourbyhour" in problems


def test_release_inspection_reads_the_classes_that_r8_kept(tmp_path: Path) -> None:
    mapping = tmp_path / "publicRelease" / "mapping.txt"
    mapping.parent.mkdir()
    mapping.write_text(
        "# compiler: R8\n"
        "com.ahuguet.castellsenvena.MainActivity -> com.ahuguet.castellsenvena.MainActivity:\n"
        "    void onCreate(android.os.Bundle) -> onCreate\n"
        "com.ahuguet.castellsenvena.feature.hourbyhour.ui.HourByHourScreenKt -> a.b:\n"
    )

    assert verify_android_mapping(mapping, PUBLIC) == [
        "publicRelease: the release keeps classes of com.ahuguet.castellsenvena.feature.hourbyhour"
    ]


def test_the_android_command_says_what_it_checked(tmp_path: Path) -> None:
    outputs = fake_android_outputs(tmp_path, PUBLIC_PACKAGES)

    result = run_inspection("android", "public", "--outputs", str(outputs))

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[:2] == [
        "Checked the public Android app: it contains what its profile allows and nothing else.",
        "- application id com.ahuguet.castellsenvena",
    ]


def test_the_android_command_fails_on_internal_code_or_a_missing_apk(tmp_path: Path) -> None:
    outputs = fake_android_outputs(tmp_path, [*PUBLIC_PACKAGES, "com.google.firebase"])

    leaking = run_inspection("android", "public", "--outputs", str(outputs))
    (outputs / "apk" / "public" / "release" / "app.apk").unlink()
    incomplete = run_inspection("android", "public", "--outputs", str(outputs))

    assert (leaking.returncode, leaking.stdout) == (1, "")
    assert leaking.stderr == (
        "Error: the public Android app: app.apk: contains classes of com.google.firebase\n"
    )
    assert (incomplete.returncode, incomplete.stdout) == (1, "")
    assert incomplete.stderr == (
        "Error: the public Android app: no public release APK; "
        "build it with make android-build CASTELLS_BUILD_PROFILE=public\n"
    )


# --- iOS ---------------------------------------------------------------------------------------


def test_ios_app_inspection_rejects_internal_modules_in_the_public_app(tmp_path: Path) -> None:
    shared = sorted(SHARED_SWIFT_MODULES)
    public = fake_ios_app(tmp_path, PUBLIC.ios_bundle_identifier, PUBLIC.display_name, shared)
    assert verify_ios_app(public, PUBLIC) == []

    (tmp_path / "leaking").mkdir()
    leaking = fake_ios_app(
        tmp_path / "leaking",
        PUBLIC.ios_bundle_identifier,
        PUBLIC.display_name,
        [*shared, "FeatureHourByHour"],
    )
    assert verify_ios_app(leaking, PUBLIC) == ["App.app: links FeatureHourByHour"]
    assert "App.app: does not link FeatureAgenda" in verify_ios_app(public, INTERNAL)


def test_ios_build_settings_inspection_keeps_push_entitlements_internal() -> None:
    public = {"PRODUCT_BUNDLE_IDENTIFIER": PUBLIC.ios_bundle_identifier}
    internal = {
        "PRODUCT_BUNDLE_IDENTIFIER": INTERNAL.ios_bundle_identifier,
        "CODE_SIGN_ENTITLEMENTS": xcode_targets()[INTERNAL.ios_scheme].configurations["Release"][
            "CODE_SIGN_ENTITLEMENTS"
        ],
        "APS_ENVIRONMENT": "production",
    }

    assert verify_ios_build_settings(public, PUBLIC) == []
    assert verify_ios_build_settings(internal, INTERNAL) == []
    assert verify_ios_build_settings(public | {"APS_ENVIRONMENT": "production"}, PUBLIC) == [
        "the public app has entitlements for push notifications"
    ]
    assert verify_ios_build_settings(internal, PUBLIC) == [
        f"the bundle identifier is {INTERNAL.ios_bundle_identifier}",
        "the public app has entitlements for push notifications",
    ]


def test_the_ios_command_checks_the_app_and_the_settings_of_its_scheme(tmp_path: Path) -> None:
    modules = sorted(SHARED_SWIFT_MODULES)
    app = fake_ios_app(tmp_path, PUBLIC.ios_bundle_identifier, PUBLIC.display_name, modules)
    tools = fake_xcodebuild(tmp_path, {"PRODUCT_BUNDLE_IDENTIFIER": PUBLIC.ios_bundle_identifier})

    result = run_inspection("ios", "public", "--app", str(app), tools=tools)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == (
        "Checked the public iOS app: it contains what its profile allows and nothing else."
    )
    assert result.stdout.splitlines()[-1] == "- entitlements for push notifications: none"
    arguments = (tools / "xcodebuild.arguments").read_text().splitlines()
    assert arguments[arguments.index("-scheme") + 1] == PUBLIC.ios_scheme
    assert arguments[arguments.index("-configuration") + 1] == "Release"


def test_the_ios_command_fails_when_the_public_app_can_receive_push(tmp_path: Path) -> None:
    modules = sorted(SHARED_SWIFT_MODULES)
    app = fake_ios_app(tmp_path, PUBLIC.ios_bundle_identifier, PUBLIC.display_name, modules)
    settings = {
        "PRODUCT_BUNDLE_IDENTIFIER": PUBLIC.ios_bundle_identifier,
        "APS_ENVIRONMENT": "production",
    }
    tools = fake_xcodebuild(tmp_path, settings)

    result = run_inspection("ios", "public", "--app", str(app), tools=tools)

    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == (
        "Error: the public iOS app: the public app has entitlements for push notifications\n"
    )
