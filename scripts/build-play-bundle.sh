#!/usr/bin/env bash

set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/release-common.sh"

BUILD_REPOSITORY_ROOT=''
BUILD_TEMPORARY_ROOT=''
BUILD_SOURCE_DIRECTORY=''
BUILD_WORKTREE_ADDED=false
# The app that Google Play receives.
APPLICATION_ID='com.ahuguet.castellsenvena'
# Google Play refuses a larger versionCode. Unix seconds stay below it until 2036.
MAX_VERSION_CODE=2100000000

cleanup_build() {
  local exit_code=$?
  trap - EXIT
  set +e
  if [[ "$BUILD_WORKTREE_ADDED" == true && -n "$BUILD_SOURCE_DIRECTORY" ]]; then
    git -C "$BUILD_REPOSITORY_ROOT" worktree remove --force \
      "$BUILD_SOURCE_DIRECTORY" >/dev/null 2>&1
  fi
  if [[ -n "$BUILD_TEMPORARY_ROOT" ]]; then
    rm -rf -- "$BUILD_TEMPORARY_ROOT"
  fi
  exit "$exit_code"
}

usage() {
  cat <<'EOF'
Usage: scripts/build-play-bundle.sh [options]

Build the signed Google Play bundle (AAB) of the app from an exact Git ref.
The version name comes from Version.xcconfig at that ref. Upload the bundle in the
Play Console.

Options:
  --ref REF               Git ref to build (default: origin/main)
  --version-code NUMBER   versionCode from 1 to 2100000000 (default: Unix UTC timestamp)
  --output-dir DIR        Where to put the bundle (default: ~/Downloads)
  --dry-run               Print the resolved build plan without building
  -h, --help              Show this help
EOF
}

generate_version_code() {
  date -u +%s
}

fail_usage() {
  printf 'Error: %s\n' "$1" >&2
  usage >&2
  return 2
}

# Print one attribute of the bundle's manifest, such as versionCode.
manifest_value() {
  bundletool dump manifest --bundle "$1" --xpath "/manifest/@$2" 2>/dev/null
}

main() {
  local ref='origin/main'
  local version_code=''
  local output_directory="$HOME/Downloads"
  local dry_run=false

  while (($# > 0)); do
    case "$1" in
      --ref)
        (($# >= 2)) || { fail_usage '--ref requires a value'; return $?; }
        ref=$2
        shift 2
        ;;
      --version-code)
        (($# >= 2)) || { fail_usage '--version-code requires a value'; return $?; }
        version_code=$2
        shift 2
        ;;
      --output-dir)
        (($# >= 2)) || { fail_usage '--output-dir requires a value'; return $?; }
        output_directory=$2
        shift 2
        ;;
      --dry-run)
        dry_run=true
        shift
        ;;
      -h|--help)
        usage
        return 0
        ;;
      *)
        fail_usage "unknown argument: $1"
        return $?
        ;;
    esac
  done

  if [[ -z "$version_code" ]]; then
    version_code=$(generate_version_code)
  fi
  if [[ ! "$version_code" =~ ^[1-9][0-9]*$ ]] || ((version_code > MAX_VERSION_CODE)); then
    fail_usage "version code must be an integer from 1 to $MAX_VERSION_CODE: $version_code"
    return $?
  fi

  require_command git

  local script_directory repository_root
  script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  repository_root=$(git -C "$script_directory" rev-parse --show-toplevel)

  if [[ "$dry_run" == false && "$ref" == 'origin/main' ]]; then
    run_command git -C "$repository_root" fetch origin main --prune
  fi

  local source_commit
  if ! source_commit=$(git -C "$repository_root" rev-parse --verify "${ref}^{commit}"); then
    printf 'Error: Git ref does not resolve to a commit: %s\n' "$ref" >&2
    return 1
  fi

  local version_name
  version_name=$(read_marketing_version "$repository_root" "$source_commit")
  local output_path="$output_directory/castells-en-vena-$version_name-$version_code.aab"

  printf 'Source ref: %s\n' "$ref"
  printf 'Source commit: %s\n' "$source_commit"
  printf 'Version: %s\n' "$version_name"
  printf 'Version code: %s\n' "$version_code"
  printf 'Bundle: %s\n' "$output_path"

  local -a gradle_command=(
    ./gradlew
    "-Pcastells.versionCode=$version_code"
    :app:bundleRelease
  )

  if [[ "$dry_run" == true ]]; then
    print_command git -C "$repository_root" worktree add --detach '<temporary-source>' "$source_commit"
    printf '+ cd <temporary-source>/android\n'
    print_command "${gradle_command[@]}"
    printf 'No bundle was built.\n'
    return 0
  fi

  require_command bundletool
  require_command jarsigner
  if [[ -z "${ANDROID_HOME:-}" && -d "$HOME/Library/Android/sdk" ]]; then
    export ANDROID_HOME="$HOME/Library/Android/sdk"
  fi
  if [[ -z "${ANDROID_HOME:-}" ]]; then
    printf 'Error: set ANDROID_HOME to the Android SDK.\n' >&2
    return 1
  fi

  local temporary_root source_directory
  temporary_root=$(mktemp -d -t castells-en-vena-play-XXXXXXXX)
  source_directory="$temporary_root/source"

  BUILD_REPOSITORY_ROOT=$repository_root
  BUILD_TEMPORARY_ROOT=$temporary_root
  BUILD_SOURCE_DIRECTORY=$source_directory
  trap cleanup_build EXIT

  run_command git -C "$repository_root" worktree add --detach "$source_directory" "$source_commit"
  BUILD_WORKTREE_ADDED=true

  (
    cd "$source_directory/android"
    run_command "${gradle_command[@]}"
  )

  local bundle_path="$source_directory/android/app/build/outputs/bundle/release/app-release.aab"
  local built_package built_version_code built_version_name
  built_package=$(manifest_value "$bundle_path" package)
  built_version_code=$(manifest_value "$bundle_path" android:versionCode)
  built_version_name=$(manifest_value "$bundle_path" android:versionName)
  if [[ "$built_package" != "$APPLICATION_ID" ]]; then
    printf 'Error: the bundle is %s; Google Play only receives %s.\n' \
      "$built_package" "$APPLICATION_ID" >&2
    return 1
  fi
  if [[ "$built_version_code" != "$version_code" || "$built_version_name" != "$version_name" ]]; then
    printf 'Error: the bundle is %s (%s); expected %s (%s).\n' \
      "$built_version_name" "$built_version_code" "$version_name" "$version_code" >&2
    return 1
  fi
  if ! jarsigner -verify "$bundle_path" 2>/dev/null | grep -q '^jar verified\.'; then
    printf 'Error: the bundle is not signed; set castells.signing.* in ~/.gradle/gradle.properties.\n' >&2
    return 1
  fi

  mkdir -p "$output_directory"
  cp "$bundle_path" "$output_path"
  printf 'Bundle ready for Google Play: %s %s (%s), commit %s.\n' \
    "$built_package" "$version_name" "$version_code" "$source_commit"
  printf 'Upload %s in the Play Console.\n' "$output_path"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
