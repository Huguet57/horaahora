"""The Gradle projects of the Android app, and what the variants of each flavor depend on.

The build files are Kotlin scripts. The expressions below read the declarations this build uses:
`implementation(projects.core.data)` or `implementation(project(":core:data"))`,
`"internalImplementation"(libs.firebase.messaging)` and, in the convention plugins,
`add("implementation", project(":core:designsystem"))`.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from scripts.app_profiles.profiles import ANDROID_ROOT, PROFILES

_PROJECT_DEPENDENCY = re.compile(
    r'(?P<configuration>"?\w+"?)\(\s*'
    r'(?:projects\.(?P<accessor>[\w.]+)|project\(\s*"(?P<path>:[\w:]+)"\s*\))\s*\)'
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


def gradle_project_dir(project: str, root: Path = ANDROID_ROOT) -> Path:
    return root.joinpath(*project.strip(":").split(":"))


def gradle_build_file(project: str, root: Path = ANDROID_ROOT) -> Path:
    return gradle_project_dir(project, root) / "build.gradle.kts"


def gradle_project_dependencies(project: str, root: Path = ANDROID_ROOT) -> dict[str, set[str]]:
    """The project dependencies of a module, by configuration, with its convention plugins'."""
    text = gradle_build_file(project, root).read_text()
    dependencies: dict[str, set[str]] = defaultdict(set)
    for match in _PROJECT_DEPENDENCY.finditer(text):
        path = match["path"] or ":" + match["accessor"].replace(".", ":")
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


def kotlin_package(source: Path) -> str | None:
    match = re.search(r"^package\s+([\w.]+)", source.read_text(), re.M)
    return match[1] if match else None
