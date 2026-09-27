from __future__ import annotations

import plistlib
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
PRODUCTION_API = "https://castells-superapp-poc.vercel.app"
IOS_PROJECT = REPOSITORY_ROOT / "HoraAHoraApp" / "HoraAHoraApp.xcodeproj" / "project.pbxproj"
IOS_APP = REPOSITORY_ROOT / "HoraAHoraApp" / "HoraAHoraApp"
IOS_DEBUG_XCCONFIG = IOS_APP / "Configuration" / "Debug.xcconfig"
ANDROID_ROOT = REPOSITORY_ROOT / "android"


def app_build_configuration(name: str) -> str:
    """The build configuration of the app target, not the project-level one."""
    project = IOS_PROJECT.read_text()
    blocks = re.findall(
        rf"\t\t\w+ /\* {name} \*/ = {{\n\t\t\tisa = XCBuildConfiguration;.*?\n\t\t}};",
        project,
        flags=re.S,
    )
    app_blocks = [
        block
        for block in blocks
        if "PRODUCT_BUNDLE_IDENTIFIER = com.ahuguet.castellsenvena;" in block
    ]
    assert len(app_blocks) == 1
    return app_blocks[0]


def gradle_block(source: str, name: str) -> str:
    match = re.search(rf"\n\s*{name} {{\n(.*?)\n\s*}}\n", source, flags=re.S)
    assert match is not None
    return match.group(1)


def test_ios_info_plist_reads_the_backend_from_the_build_settings() -> None:
    # Xcode only generates the INFOPLIST_KEY_ settings it knows, so custom keys and the
    # ATS dictionary live in a real Info.plist that it merges with the generated one.
    project = IOS_PROJECT.read_text()
    info = plistlib.loads((IOS_APP / "Info.plist").read_bytes())

    assert info["CastellsAPIBaseURL"] == "$(CASTELLS_API_BASE_URL)"
    assert info["NSAppTransportSecurity"] == {"NSAllowsLocalNetworking": True}
    for configuration in ("Debug", "Release"):
        assert "INFOPLIST_FILE = HoraAHoraApp/Info.plist;" in app_build_configuration(configuration)
    assert "INFOPLIST_KEY_CastellsAPIBaseURL" not in project
    assert "INFOPLIST_KEY_NSAppTransportSecurity" not in project


def test_ios_release_builds_always_use_the_production_backend() -> None:
    release = app_build_configuration("Release")

    assert f'CASTELLS_API_BASE_URL = "{PRODUCTION_API}";' in release
    assert "baseConfigurationReference" not in release


def test_ios_debug_builds_use_the_local_backend_unless_this_mac_overrides_it() -> None:
    debug = app_build_configuration("Debug")
    project = IOS_PROJECT.read_text()
    xcconfig = IOS_DEBUG_XCCONFIG.read_text()

    assert "CASTELLS_API_BASE_URL" not in debug
    reference = re.search(r"baseConfigurationReference = (\w+) /\* Debug\.xcconfig \*/;", debug)
    assert reference is not None
    assert (
        f"{reference.group(1)} /* Debug.xcconfig */ = {{isa = PBXFileReference; "
        "lastKnownFileType = text.xcconfig; path = Debug.xcconfig;" in project
    )
    default = "CASTELLS_API_BASE_URL = http:/$()/127.0.0.1:8000"
    override = '#include? "Debug.local.xcconfig"'
    assert default in xcconfig
    assert override in xcconfig
    assert xcconfig.index(override) > xcconfig.index(default)
    assert "*.local.xcconfig" in (REPOSITORY_ROOT / ".gitignore").read_text().splitlines()


def test_android_release_builds_use_production_and_debug_builds_the_local_backend() -> None:
    properties = (ANDROID_ROOT / "gradle.properties").read_text().splitlines()
    build = (ANDROID_ROOT / "app" / "build.gradle.kts").read_text()

    assert f"castells.apiBaseUrl={PRODUCTION_API}" in properties
    assert "castells.apiBaseUrl.debug=http://10.0.2.2:8000" in properties
    assert "API_BASE_URL" not in gradle_block(build, "defaultConfig")
    assert '"API_BASE_URL", "\\"$debugApiBaseUrl\\""' in gradle_block(build, "debug")
    assert '"API_BASE_URL", "\\"$releaseApiBaseUrl\\""' in gradle_block(build, "release")
    release_url = re.search(r"val releaseApiBaseUrl: String = (.*?)\n\n", build, flags=re.S)
    assert release_url is not None
    assert 'providers.gradleProperty("castells.apiBaseUrl")' in release_url.group(1)
    assert "CASTELLS_API_BASE_URL" not in release_url.group(1)


def test_the_local_backend_database_is_reachable_only_from_this_computer() -> None:
    # Debug builds rely on the local backend, and the README runs alembic, the jobs and
    # uvicorn from the host against the Compose database.
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text()
    database = compose.split("\n  db:\n", 1)[1].split("\n\n", 1)[0]

    assert '- "127.0.0.1:5432:5432"' in database
