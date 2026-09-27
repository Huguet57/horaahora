"""The inspection of the APKs and the R8 mapping that `make android-build` leaves for a profile."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from scripts.app_profiles.profiles import (
    INTERNAL,
    INTERNAL_KOTLIN_PACKAGES,
    INTERNAL_MANIFEST_ENTRIES,
    PUBLIC,
    PUBLIC_FORBIDDEN_MANIFEST_ENTRIES,
    SHARED_KOTLIN_PACKAGES,
    Profile,
    in_packages,
)


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
    if not _contains(manifest, profile.android_application_id):
        problems.append(f"{apk.name}: the manifest is not {profile.android_application_id}")
    if profile is PUBLIC:
        if _contains(manifest, INTERNAL.android_application_id):
            problems.append(f"{apk.name}: the manifest names {INTERNAL.android_application_id}")
        problems.extend(
            f"{apk.name}: the manifest declares {entry}"
            for entry in PUBLIC_FORBIDDEN_MANIFEST_ENTRIES
            if _contains(manifest, entry)
        )
    else:
        problems.extend(
            f"{apk.name}: the manifest does not declare {entry}"
            for entry in INTERNAL_MANIFEST_ENTRIES
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
    """Problems with the R8 mapping of a public release APK: internal classes it kept."""
    if profile is not PUBLIC:
        return []
    kept = [
        line.split(" -> ", 1)[0]
        for line in mapping.read_text().splitlines()
        if line and not line.startswith((" ", "#")) and " -> " in line
    ]
    return [
        f"{mapping.parent.name}: the release keeps classes of {package}"
        for package in INTERNAL_KOTLIN_PACKAGES
        if any(in_packages(name, (package,)) for name in kept)
    ]


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


def android_facts(profile: Profile) -> list[str]:
    """What a successful inspection of the Android app of the profile has established."""
    internal_classes = ", ".join(INTERNAL_KOTLIN_PACKAGES)
    if profile is PUBLIC:
        profile_facts = [
            "the manifest does not declare " + ", ".join(PUBLIC_FORBIDDEN_MANIFEST_ENTRIES),
            f"the debug APK has none of the classes of {internal_classes}",
            "the release APK's R8 mapping keeps none of those classes",
        ]
    else:
        profile_facts = [
            "the manifest declares " + ", ".join(INTERNAL_MANIFEST_ENTRIES),
            f"the debug APK keeps the classes of {internal_classes}",
        ]
    return [
        f"application id {profile.android_application_id}",
        *profile_facts,
        "the calculator, the score table and the settings are in",
    ]
