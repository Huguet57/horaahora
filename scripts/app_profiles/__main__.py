"""Inspect a built app of a build profile: python3 -m scripts.app_profiles android|ios PROFILE."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.app_profiles.android_inspection import android_facts, verify_android_outputs
from scripts.app_profiles.ios_inspection import (
    ios_facts,
    read_ios_build_settings,
    verify_ios_app,
    verify_ios_build_settings,
)
from scripts.app_profiles.profiles import ANDROID_ROOT, PROFILES


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m scripts.app_profiles",
        description="Inspect a built app of a build profile.",
    )
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
        subject = f"the {profile.name} Android app"
        problems = verify_android_outputs(options.outputs, profile)
        facts = android_facts(profile)
    else:
        subject = f"the {profile.name} iOS app"
        problems = [
            *verify_ios_app(options.app, profile),
            *verify_ios_build_settings(
                read_ios_build_settings(profile, options.configuration), profile
            ),
        ]
        facts = ios_facts(profile)
    for problem in problems:
        print(f"Error: {subject}: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"Checked {subject}: it contains what its profile allows and nothing else.")
    for fact in facts:
        print(f"- {fact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
