"""The iOS and Android apps take their visible version from Version.xcconfig, and only from there."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).parents[1]
VERSION_FILE = REPOSITORY_ROOT / "Version.xcconfig"
XCODE_PROJECT = REPOSITORY_ROOT / "HoraAHoraApp" / "HoraAHoraApp.xcodeproj"
ANDROID_APP_BUILD = REPOSITORY_ROOT / "android" / "app" / "build.gradle.kts"


def marketing_version() -> str:
    settings = re.findall(r"^MARKETING_VERSION = (\S+)$", VERSION_FILE.read_text(), re.MULTILINE)
    assert len(settings) == 1
    return settings[0]


def test_the_version_file_holds_one_numeric_version() -> None:
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", marketing_version())


def test_the_xcode_project_does_not_set_its_own_version() -> None:
    project = (XCODE_PROJECT / "project.pbxproj").read_text()

    assert "MARKETING_VERSION" not in project
    assert "path = ../Version.xcconfig;" in project


def test_the_android_app_does_not_set_its_own_version_name() -> None:
    build = ANDROID_APP_BUILD.read_text()

    assert not re.search(r"versionName\s*=\s*\"", build)
    assert "Version.xcconfig" in build


@pytest.mark.skipif(
    sys.platform != "darwin" or shutil.which("xcodebuild") is None,
    reason="Reading Xcode build settings requires xcodebuild",
)
@pytest.mark.parametrize("configuration", ["Debug", "Release"])
def test_xcode_builds_take_the_version_from_the_version_file(configuration: str) -> None:
    result = subprocess.run(
        [
            "xcodebuild",
            "-showBuildSettings",
            "-project",
            str(XCODE_PROJECT),
            "-scheme",
            "HoraAHoraApp",
            "-configuration",
            configuration,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"    MARKETING_VERSION = {marketing_version()}\n" in result.stdout
