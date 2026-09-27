"""The app targets of the Xcode project and its shared schemes, read from their files.

project.pbxproj is an old-style (OpenStep) property list, which plistlib does not read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

from scripts.app_profiles.profiles import IOS_PROJECT


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
