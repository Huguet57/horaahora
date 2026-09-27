"""The products and targets of CastellsKit's Package.swift, and what Swift sources import."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from scripts.app_profiles.profiles import SWIFT_PACKAGE


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
