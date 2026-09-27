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


def android_facts(profile: Profile) -> list[str]:
    """What a successful inspection of the Android app of the profile has established."""
    kept = "keeps" if profile is INTERNAL else "has none of"
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
