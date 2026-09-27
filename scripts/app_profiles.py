"""The public and internal builds of the apps, and the checks that keep them apart.

The public app, the one in the App Store and on Google Play, has the calculator, the score table
and their settings. The internal app is a separate development app, with its own identifier and
name: it adds Hora a Hora, Agenda, their settings and the news notifications. The build profile,
CASTELLS_BUILD_PROFILE=public|internal, chooses which one a build produces; `public` is the
default.

The functions below read the Xcode project, the Swift package and the Gradle build, so the tests
can check that no internal module or entry point reaches the public app. They also inspect built
apps; CI runs them after building each profile (see the Makefile):

    python3 -m scripts.app_profiles android public
    python3 -m scripts.app_profiles ios public --app build/ios/public/.../HoraAHoraApp.app

Only the standard library is used, so the inspection also runs on the macOS CI runners.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
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
    {"FeatureHourByHour", "FeatureAgenda", "FeatureInternalSettings"}
)

# The Gradle projects only the internal app depends on.
INTERNAL_GRADLE_PROJECTS = frozenset(
    {
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
# The code of the internal sections, of the news notifications and of Firebase.
INTERNAL_KOTLIN_PACKAGES = (
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


# --- Xcode project -----------------------------------------------------------------------------


class _OpenStepParser:
    """The old-style property list format of project.pbxproj."""

    _UNQUOTED = re.compile(r"[A-Za-z0-9_$+/:.\-]+")
    _ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}

    def __init__(self, text: str) -> None:
        self.text = text
        self.index = 0

    def parse(self) -> Any:
        value = self._value()
        self._skip()
        if self.index != len(self.text):
            raise ValueError(f"Unexpected text at offset {self.index}")
        return value

    def _skip(self) -> None:
        while self.index < len(self.text):
            if self.text[self.index].isspace():
                self.index += 1
            elif self.text.startswith("/*", self.index):
                self.index = self.text.index("*/", self.index + 2) + 2
            elif self.text.startswith("//", self.index):
                end = self.text.find("\n", self.index)
                self.index = len(self.text) if end == -1 else end + 1
            else:
                return

    def _expect(self, character: str) -> None:
        self._skip()
        if self.text[self.index] != character:
            raise ValueError(f"Expected {character!r} at offset {self.index}")
        self.index += 1

    def _value(self) -> Any:
        self._skip()
        character = self.text[self.index]
        if character == "{":
            return self._dictionary()
        if character == "(":
            return self._array()
        if character == '"':
            return self._quoted()
        match = self._UNQUOTED.match(self.text, self.index)
        if match is None:
            raise ValueError(f"Unexpected {character!r} at offset {self.index}")
        self.index = match.end()
        return match.group()

    def _dictionary(self) -> dict[str, Any]:
        self.index += 1
        result: dict[str, Any] = {}
        while True:
            self._skip()
            if self.text[self.index] == "}":
                self.index += 1
                return result
            key = self._value()
            self._expect("=")
            result[key] = self._value()
            self._expect(";")

    def _array(self) -> list[Any]:
        self.index += 1
        result: list[Any] = []
        while True:
            self._skip()
            if self.text[self.index] == ")":
                self.index += 1
                return result
            result.append(self._value())
            self._skip()
            if self.text[self.index] == ",":
                self.index += 1

    def _quoted(self) -> str:
        self.index += 1
        characters: list[str] = []
        while self.text[self.index] != '"':
            if self.text[self.index] == "\\":
                escaped = self.text[self.index + 1]
                characters.append(self._ESCAPES.get(escaped, escaped))
                self.index += 2
            else:
                characters.append(self.text[self.index])
                self.index += 1
        self.index += 1
        return "".join(characters)


def parse_openstep_plist(text: str) -> Any:
    return _OpenStepParser(text).parse()


@dataclass(frozen=True)
class XcodeTarget:
    name: str
    # The Swift package products the target depends on, and the ones it links.
    products: frozenset[str]
    linked_products: frozenset[str]
    # Paths relative to the folder of the Xcode project.
    sources: tuple[str, ...]
    resources: tuple[str, ...]
    # Build settings by configuration name, and the .xcconfig each configuration is based on.
    configurations: dict[str, dict[str, Any]]
    base_configurations: dict[str, str | None]


def xcode_targets(project: Path = IOS_PROJECT) -> dict[str, XcodeTarget]:
    document = parse_openstep_plist((project / "project.pbxproj").read_text())
    objects: dict[str, dict[str, Any]] = document["objects"]
    root = objects[document["rootObject"]]
    paths = _xcode_paths(objects, root["mainGroup"])

    targets = {}
    for target_id in root["targets"]:
        target = objects[target_id]
        phases = [objects[phase] for phase in target.get("buildPhases", [])]

        def phase_files(isa: str, phases: list[dict[str, Any]] = phases) -> list[dict[str, Any]]:
            return [
                objects[build_file]
                for phase in phases
                if phase["isa"] == isa
                for build_file in phase.get("files", [])
            ]

        configurations = [
            objects[configuration]
            for configuration in objects[target["buildConfigurationList"]]["buildConfigurations"]
        ]
        targets[target["name"]] = XcodeTarget(
            name=target["name"],
            products=frozenset(
                objects[dependency]["productName"]
                for dependency in target.get("packageProductDependencies", [])
            ),
            linked_products=frozenset(
                objects[file["productRef"]]["productName"]
                for file in phase_files("PBXFrameworksBuildPhase")
                if "productRef" in file
            ),
            sources=tuple(paths[file["fileRef"]] for file in phase_files("PBXSourcesBuildPhase")),
            resources=tuple(
                paths[file["fileRef"]] for file in phase_files("PBXResourcesBuildPhase")
            ),
            configurations={
                configuration["name"]: configuration["buildSettings"]
                for configuration in configurations
            },
            base_configurations={
                configuration["name"]: paths.get(configuration.get("baseConfigurationReference"))
                for configuration in configurations
            },
        )
    return targets


def _xcode_paths(objects: dict[str, dict[str, Any]], main_group: str) -> dict[str, str]:
    """The path of every file and group, relative to the folder of the Xcode project."""
    paths: dict[str, str] = {}

    def visit(object_id: str, folder: PurePosixPath) -> None:
        item = objects[object_id]
        location = folder
        if item.get("path") and item.get("sourceTree", "<group>") == "<group>":
            location = folder / item["path"]
        paths[object_id] = location.as_posix()
        for child in item.get("children", []):
            visit(child, location)

    visit(main_group, PurePosixPath("."))
    return paths


def xcode_scheme(name: str, project: Path = IOS_PROJECT) -> dict[str, Any]:
    """The target a shared scheme builds and the configuration it archives."""
    import xml.etree.ElementTree as ElementTree

    scheme = ElementTree.parse(project / "xcshareddata" / "xcschemes" / f"{name}.xcscheme")
    built = [
        reference.get("BlueprintName")
        for reference in scheme.getroot().iterfind(
            "BuildAction/BuildActionEntries/BuildActionEntry/BuildableReference"
        )
    ]
    archive = scheme.getroot().find("ArchiveAction")
    return {
        "targets": built,
        "archive_configuration": None if archive is None else archive.get("buildConfiguration"),
    }


# --- Swift package -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SwiftPackage:
    # Product name to the targets it exposes.
    products: dict[str, tuple[str, ...]]
    # Target name to the targets it depends on.
    targets: dict[str, tuple[str, ...]]
    test_targets: frozenset[str]

    def closure(self, names: Iterable[str]) -> frozenset[str]:
        """The targets that the given products or targets bring, including themselves."""
        pending = [target for name in names for target in self.products.get(name, (name,))]
        found: set[str] = set()
        while pending:
            name = pending.pop()
            if name not in found:
                found.add(name)
                pending.extend(self.targets.get(name, ()))
        return frozenset(found)


def swift_package(package_file: Path = SWIFT_PACKAGE) -> SwiftPackage:
    text = package_file.read_text()
    products = {
        name: tuple(re.findall(r'"(\w+)"', targets))
        for name, targets in re.findall(
            r'\.library\(\s*name:\s*"(\w+)",\s*targets:\s*\[([^\]]*)\]', text
        )
    }
    targets: dict[str, tuple[str, ...]] = {}
    tests = set()
    for match in re.finditer(r"\.(target|testTarget)\(", text):
        arguments = _parenthesized(text, match.end() - 1)
        name = re.search(r'name:\s*"(\w+)"', arguments)
        if name is None:
            raise ValueError(f"A target without a name in {package_file}")
        dependencies = re.search(r"dependencies:\s*\[([^\]]*)\]", arguments)
        targets[name.group(1)] = (
            tuple(re.findall(r'"(\w+)"', dependencies.group(1))) if dependencies else ()
        )
        if match.group(1) == "testTarget":
            tests.add(name.group(1))
    return SwiftPackage(products=products, targets=targets, test_targets=frozenset(tests))


def _parenthesized(text: str, opening: int) -> str:
    """The text between the parenthesis at `opening` and the one that closes it."""
    depth = 0
    index = opening
    while index < len(text):
        character = text[index]
        if character == '"':
            index = text.index('"', index + 1)
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return text[opening + 1 : index]
        index += 1
    raise ValueError("Unbalanced parentheses")


def swift_imports(source: Path) -> frozenset[str]:
    return frozenset(
        re.findall(r"^\s*(?:@testable\s+)?import\s+(?:\w+\s+)?(\w+)", source.read_text(), re.M)
    )


# --- Gradle ------------------------------------------------------------------------------------

_PROJECT_DEPENDENCY = re.compile(
    r'(?P<configuration>"?\w+"?)\(\s*projects\.(?P<accessor>[\w.]+)\s*\)'
)
_CATALOG_DEPENDENCY = re.compile(
    r'(?P<configuration>"?\w+"?)\(\s*(?:platform\(\s*)?libs\.(?P<alias>[\w.]+)'
)
_CONVENTION_DEPENDENCY = re.compile(
    r'add\(\s*"(?P<configuration>\w+)",\s*project\("(?P<project>:[\w:]+)"\)\s*\)'
)
# Configurations whose dependencies end up in, or compile against, an app variant.
_LIBRARY_CONFIGURATIONS = ("api", "implementation", "runtimeOnly", "compileOnly")


def gradle_projects(root: Path = ANDROID_ROOT) -> frozenset[str]:
    settings = (root / "settings.gradle.kts").read_text()
    projects: set[str] = set()
    for arguments in re.findall(r"include\((.*?)\)", settings, flags=re.S):
        projects.update(re.findall(r'"(:[\w:]+)"', arguments))
    return frozenset(projects)


def gradle_build_file(project: str, root: Path = ANDROID_ROOT) -> Path:
    return root.joinpath(*project.strip(":").split(":"), "build.gradle.kts")


def gradle_project_dependencies(project: str, root: Path = ANDROID_ROOT) -> dict[str, set[str]]:
    """The project dependencies of a module, by configuration, with its convention plugins'."""
    text = gradle_build_file(project, root).read_text()
    dependencies: dict[str, set[str]] = defaultdict(set)
    for match in _PROJECT_DEPENDENCY.finditer(text):
        path = ":" + match["accessor"].replace(".", ":")
        dependencies[match["configuration"].strip('"')].add(path)
    conventions = _convention_dependencies(root)
    for plugin in re.findall(r'id\("([\w.]+)"\)', text):
        for configuration, dependency in conventions.get(plugin, ()):
            dependencies[configuration].add(dependency)
    return dependencies


def gradle_catalog_dependencies(project: str, root: Path = ANDROID_ROOT) -> dict[str, set[str]]:
    """The version catalog aliases a module depends on, by configuration."""
    text = gradle_build_file(project, root).read_text()
    dependencies: dict[str, set[str]] = defaultdict(set)
    for match in _CATALOG_DEPENDENCY.finditer(text):
        dependencies[match["configuration"].strip('"')].add(match["alias"])
    return dependencies


def _convention_dependencies(root: Path) -> dict[str, list[tuple[str, str]]]:
    """The project dependencies each convention plugin adds, by plugin id."""
    convention = root / "build-logic" / "convention"
    registrations = re.findall(
        r'id = "([\w.]+)"\s*\n\s*implementationClass = "(\w+)"',
        (convention / "build.gradle.kts").read_text(),
    )
    sources = {path.stem: path.read_text() for path in convention.rglob("*.kt")}

    def added(plugin_class: str) -> list[tuple[str, str]]:
        source = sources.get(plugin_class, "")
        found = [
            (m["configuration"], m["project"]) for m in _CONVENTION_DEPENDENCY.finditer(source)
        ]
        for applied in re.findall(r"pluginManager\.apply\((\w+)::class", source):
            found.extend(added(applied))
        return found

    return {plugin: added(plugin_class) for plugin, plugin_class in registrations}


def _app_configuration_applies(configuration: str, flavor: str) -> bool:
    """Whether an :app configuration reaches the variants of the flavor (tests excluded)."""
    if configuration.startswith(("test", "androidTest", "kapt", "ksp")):
        return False
    other_flavors = [name for name in PROFILES if name != flavor]
    return not configuration.startswith(tuple(other_flavors))


def android_variant_projects(flavor: str, root: Path = ANDROID_ROOT) -> frozenset[str]:
    """The Gradle projects that the app variants of a flavor contain."""
    app = gradle_project_dependencies(":app", root)
    pending = [
        dependency
        for configuration, dependencies in app.items()
        if _app_configuration_applies(configuration, flavor)
        for dependency in dependencies
    ]
    found: set[str] = set()
    while pending:
        project = pending.pop()
        if project in found:
            continue
        found.add(project)
        for configuration, dependencies in gradle_project_dependencies(project, root).items():
            if configuration in _LIBRARY_CONFIGURATIONS:
                pending.extend(dependencies)
    return frozenset(found)


def android_variant_libraries(flavor: str, root: Path = ANDROID_ROOT) -> frozenset[str]:
    """The version catalog aliases the :app module adds to the variants of a flavor."""
    return frozenset(
        alias
        for configuration, aliases in gradle_catalog_dependencies(":app", root).items()
        if _app_configuration_applies(configuration, flavor)
        for alias in aliases
    )


def kotlin_imports(source: Path) -> frozenset[str]:
    return frozenset(re.findall(r"^import\s+([\w.]+)", source.read_text(), re.M))


# --- Built apps --------------------------------------------------------------------------------


def _contains(data: bytes, text: str) -> bool:
    """Whether binary data holds the text, in UTF-8 or in the UTF-16 of binary XML."""
    return text.encode() in data or text.encode("utf-16-le") in data


def _dex_descriptor(package: str) -> str:
    return "L" + package.replace(".", "/") + "/"


def verify_android_apk(apk: Path, profile: Profile, *, minified: bool) -> list[str]:
    """Problems with an APK of the profile. Class names are only checked if not minified."""
    problems = []
    with zipfile.ZipFile(apk) as archive:
        manifest = archive.read("AndroidManifest.xml")
        dex = b"".join(
            archive.read(name)
            for name in archive.namelist()
            if re.fullmatch(r"classes\d*\.dex", name)
        )
    other = INTERNAL if profile is PUBLIC else PUBLIC
    if not _contains(manifest, profile.android_application_id):
        problems.append(f"{apk.name}: the manifest is not {profile.android_application_id}")
    if profile is PUBLIC:
        if _contains(manifest, other.android_application_id):
            problems.append(f"{apk.name}: the manifest names {other.android_application_id}")
        problems.extend(
            f"{apk.name}: the manifest declares {entry}"
            for entry in INTERNAL_MANIFEST_ENTRIES
            if _contains(manifest, entry)
        )
    else:
        problems.extend(
            f"{apk.name}: the manifest does not declare {entry}"
            for entry in INTERNAL_MANIFEST_ENTRIES[:2]
            if not _contains(manifest, entry)
        )
    if minified:
        return problems

    for package in SHARED_KOTLIN_PACKAGES:
        if not _contains(dex, _dex_descriptor(package)):
            problems.append(f"{apk.name}: no classes of {package}")
    for package in INTERNAL_KOTLIN_PACKAGES:
        present = _contains(dex, _dex_descriptor(package))
        if profile is PUBLIC and present:
            problems.append(f"{apk.name}: contains classes of {package}")
        if profile is INTERNAL and not present:
            problems.append(f"{apk.name}: no classes of {package}")
    return problems


def verify_android_mapping(mapping: Path, profile: Profile) -> list[str]:
    """Problems with the R8 mapping of a release APK: the classes it kept, by original name."""
    kept = [
        line.split(" -> ", 1)[0]
        for line in mapping.read_text().splitlines()
        if line and not line.startswith((" ", "#")) and " -> " in line
    ]
    problems = []
    for package in INTERNAL_KOTLIN_PACKAGES:
        present = any(in_packages(name, (package,)) for name in kept)
        if profile is PUBLIC and present:
            problems.append(f"{mapping.parent.name}: the release keeps classes of {package}")
    return problems


def verify_android_outputs(outputs: Path, profile: Profile) -> list[str]:
    """Problems with the debug and release APKs that `make android-build` leaves in outputs."""
    flavor = profile.name
    debug = sorted((outputs / "apk" / flavor / "debug").glob("*.apk"))
    release = sorted((outputs / "apk" / flavor / "release").glob("*.apk"))
    mapping = outputs / "mapping" / f"{flavor}Release" / "mapping.txt"
    missing = [
        f"no {description}; build it with make android-build CASTELLS_BUILD_PROFILE={flavor}"
        for description, found in (
            (f"{flavor} debug APK", len(debug) == 1),
            (f"{flavor} release APK", len(release) == 1),
            (f"{flavor} release R8 mapping", mapping.is_file()),
        )
        if not found
    ]
    if missing:
        return missing
    return [
        *verify_android_apk(debug[0], profile, minified=False),
        *verify_android_apk(release[0], profile, minified=True),
        *verify_android_mapping(mapping, profile),
    ]


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


def verified_facts(platform: str, profile: Profile) -> list[str]:
    """What a successful inspection of an app of the profile has established."""
    kept = "keeps" if profile is INTERNAL else "has none of"
    if platform == "android":
        return [
            f"application id {profile.android_application_id}",
            f"the manifest {'declares' if profile is INTERNAL else 'does not declare'} "
            + ", ".join(INTERNAL_MANIFEST_ENTRIES[: 2 if profile is INTERNAL else 3]),
            f"the debug APK {kept} the classes of " + ", ".join(INTERNAL_KOTLIN_PACKAGES),
            *(
                ["the release APK's R8 mapping keeps none of those classes"]
                if profile is PUBLIC
                else []
            ),
            "the calculator, the score table and the settings are in",
        ]
    return [
        f"bundle identifier {profile.ios_bundle_identifier}, named «{profile.display_name}»",
        f"the executable {'links' if profile is INTERNAL else 'does not link'} "
        + ", ".join(sorted(INTERNAL_SWIFT_MODULES)),
        "the executable links " + ", ".join(sorted(SHARED_SWIFT_MODULES - {"CastellsDomain"})),
        "entitlements for push notifications"
        + (" (aps-environment)" if profile is INTERNAL else ": none"),
    ]


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a built app of a build profile.")
    platforms = parser.add_subparsers(dest="platform", required=True)
    android = platforms.add_parser("android", help="the APKs left by make android-build")
    android.add_argument("profile", choices=PROFILES)
    android.add_argument("--outputs", type=Path, default=ANDROID_ROOT / "app" / "build" / "outputs")
    ios = platforms.add_parser("ios", help="an app built with make ios-build")
    ios.add_argument("profile", choices=PROFILES)
    ios.add_argument("--app", type=Path, required=True)
    ios.add_argument("--configuration", default="Release")
    options = parser.parse_args(arguments)

    profile = PROFILES[options.profile]
    if options.platform == "android":
        problems = verify_android_outputs(options.outputs, profile)
        subject = f"the {profile.name} Android app"
    else:
        problems = [
            *verify_ios_app(options.app, profile),
            *verify_ios_build_settings(
                read_ios_build_settings(profile, options.configuration), profile
            ),
        ]
        subject = f"the {profile.name} iOS app"
    for problem in problems:
        print(f"Error: {subject}: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"Checked {subject}: it contains what its profile allows and nothing else.")
    for fact in verified_facts(options.platform, profile):
        print(f"- {fact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
