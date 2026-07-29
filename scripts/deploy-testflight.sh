#!/usr/bin/env bash

set -euo pipefail

DEPLOY_REPOSITORY_ROOT=''
DEPLOY_TEMPORARY_ROOT=''
DEPLOY_SOURCE_DIRECTORY=''
DEPLOY_WORKTREE_ADDED=false
DEPLOY_KEEP_ARTIFACTS=false

cleanup_deploy() {
  local exit_code=$?
  trap - EXIT
  set +e
  if [[ "$DEPLOY_WORKTREE_ADDED" == true && -n "$DEPLOY_SOURCE_DIRECTORY" ]]; then
    git -C "$DEPLOY_REPOSITORY_ROOT" worktree remove --force \
      "$DEPLOY_SOURCE_DIRECTORY" >/dev/null 2>&1
  fi
  if [[ "$DEPLOY_KEEP_ARTIFACTS" == true ]]; then
    printf 'Artifacts kept at: %s\n' "$DEPLOY_TEMPORARY_ROOT"
  elif [[ -n "$DEPLOY_TEMPORARY_ROOT" ]]; then
    rm -rf -- "$DEPLOY_TEMPORARY_ROOT"
  fi
  exit "$exit_code"
}

usage() {
  cat <<'EOF'
Usage: scripts/deploy-testflight.sh [options]

Build and upload Castells en vena to TestFlight from an exact Git ref.

Options:
  --ref REF                 Git ref to deploy (default: origin/main)
  --marketing-version VER   Override CFBundleShortVersionString (for example: 1.1)
  --build-number NUMBER     Positive integer build number (default: Unix UTC timestamp)
  --skip-tests              Skip Python and Swift tests
  --dry-run                 Print the resolved deploy plan without building or uploading
  --keep-artifacts          Keep the temporary archive and upload artifacts after exit
  -h, --help                Show this help
EOF
}

generate_build_number() {
  date -u +%s
}

fail_usage() {
  printf 'Error: %s\n' "$1" >&2
  usage >&2
  return 2
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$1" >&2
    return 1
  fi
}

print_command() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
}

run_command() {
  print_command "$@"
  "$@"
}

main() {
  local ref='origin/main'
  local marketing_version=''
  local build_number=''
  local skip_tests=false
  local dry_run=false
  local keep_artifacts=false

  while (($# > 0)); do
    case "$1" in
      --ref)
        (($# >= 2)) || { fail_usage '--ref requires a value'; return $?; }
        ref=$2
        shift 2
        ;;
      --build-number)
        (($# >= 2)) || { fail_usage '--build-number requires a value'; return $?; }
        build_number=$2
        shift 2
        ;;
      --marketing-version)
        (($# >= 2)) || { fail_usage '--marketing-version requires a value'; return $?; }
        marketing_version=$2
        shift 2
        ;;
      --skip-tests)
        skip_tests=true
        shift
        ;;
      --dry-run)
        dry_run=true
        shift
        ;;
      --keep-artifacts)
        keep_artifacts=true
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

  if [[ -z "$build_number" ]]; then
    build_number=$(generate_build_number)
  fi
  if [[ ! "$build_number" =~ ^[1-9][0-9]*$ ]]; then
    fail_usage "build number must be a positive integer: $build_number"
    return $?
  fi
  if [[ -n "$marketing_version" && ! "$marketing_version" =~ ^[0-9]+(\.[0-9]+){1,2}$ ]]; then
    fail_usage \
      "marketing version must contain two or three numeric components: $marketing_version"
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

  printf 'Source ref: %s\n' "$ref"
  printf 'Source commit: %s\n' "$source_commit"
  if [[ -n "$marketing_version" ]]; then
    printf 'Marketing version: %s\n' "$marketing_version"
  else
    printf 'Marketing version: project setting\n'
  fi
  printf 'Build number: %s\n' "$build_number"

  local -a archive_overrides=("CURRENT_PROJECT_VERSION=$build_number")
  if [[ -n "$marketing_version" ]]; then
    archive_overrides+=("MARKETING_VERSION=$marketing_version")
  fi

  if [[ "$dry_run" == true ]]; then
    print_command git -C "$repository_root" worktree add --detach '<temporary-source>' "$source_commit"
    if [[ "$skip_tests" == false ]]; then
      print_command uv sync --frozen
      print_command uv run --frozen --no-sync python -m pytest -q
      print_command swift test
    fi
    print_command xcodebuild archive \
      -project '<temporary-source>/HoraAHoraApp/HoraAHoraApp.xcodeproj' \
      -scheme HoraAHoraApp \
      -configuration Release \
      -destination 'generic/platform=iOS' \
      -archivePath '<temporary-artifacts>/CastellsEnVena.xcarchive' \
      -allowProvisioningUpdates \
      "${archive_overrides[@]}"
    print_command xcodebuild -exportArchive \
      -archivePath '<temporary-artifacts>/CastellsEnVena.xcarchive' \
      -exportOptionsPlist '<temporary-artifacts>/UploadOptions.plist' \
      -exportPath '<temporary-artifacts>/upload' \
      -allowProvisioningUpdates
    printf 'No upload was performed.\n'
    return 0
  fi

  require_command xcodebuild
  require_command plutil
  if [[ "$skip_tests" == false ]]; then
    require_command uv
    require_command swift
  fi
  if [[ ! -x /usr/libexec/PlistBuddy ]]; then
    printf 'Error: required command not found: /usr/libexec/PlistBuddy\n' >&2
    return 1
  fi

  local temporary_root source_directory artifacts_directory archive_path upload_options
  temporary_root=$(mktemp -d -t castells-en-vena-testflight-XXXXXXXX)
  source_directory="$temporary_root/source"
  artifacts_directory="$temporary_root/artifacts"
  archive_path="$artifacts_directory/CastellsEnVena.xcarchive"
  upload_options="$artifacts_directory/UploadOptions.plist"
  mkdir -p "$artifacts_directory"

  DEPLOY_REPOSITORY_ROOT=$repository_root
  DEPLOY_TEMPORARY_ROOT=$temporary_root
  DEPLOY_SOURCE_DIRECTORY=$source_directory
  DEPLOY_KEEP_ARTIFACTS=$keep_artifacts
  trap cleanup_deploy EXIT

  run_command git -C "$repository_root" worktree add --detach "$source_directory" "$source_commit"
  DEPLOY_WORKTREE_ADDED=true

  local project_path export_options_path
  project_path="$source_directory/HoraAHoraApp/HoraAHoraApp.xcodeproj"
  export_options_path="$source_directory/HoraAHoraApp/ExportOptions-TestFlight.plist"
  if [[ ! -d "$project_path" || ! -f "$export_options_path" ]]; then
    printf 'Error: the selected commit does not contain the iOS project and TestFlight export options.\n' >&2
    return 1
  fi

  if [[ "$skip_tests" == false ]]; then
    (
      cd "$source_directory"
      run_command uv sync --frozen
      run_command uv run --frozen --no-sync python -m pytest -q
    )
    (
      cd "$source_directory/HoraAHoraApp/Packages/CastellsKit"
      run_command swift test
    )
  fi

  run_command xcodebuild archive \
    -project "$project_path" \
    -scheme HoraAHoraApp \
    -configuration Release \
    -destination 'generic/platform=iOS' \
    -archivePath "$archive_path" \
    -allowProvisioningUpdates \
    "${archive_overrides[@]}"

  local archived_build archived_version bundle_identifier
  archived_build=$(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleVersion' "$archive_path/Info.plist")
  archived_version=$(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleShortVersionString' "$archive_path/Info.plist")
  bundle_identifier=$(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleIdentifier' "$archive_path/Info.plist")
  if [[ "$archived_build" != "$build_number" ]]; then
    printf 'Error: archived build is %s; expected %s.\n' "$archived_build" "$build_number" >&2
    return 1
  fi
  if [[ -n "$marketing_version" && "$archived_version" != "$marketing_version" ]]; then
    printf 'Error: archived version is %s; expected %s.\n' \
      "$archived_version" "$marketing_version" >&2
    return 1
  fi

  cp "$export_options_path" "$upload_options"
  plutil -replace destination -string upload "$upload_options"

  printf 'Uploading %s %s (%s) to App Store Connect...\n' \
    "$bundle_identifier" "$archived_version" "$archived_build"
  run_command xcodebuild -exportArchive \
    -archivePath "$archive_path" \
    -exportOptionsPlist "$upload_options" \
    -exportPath "$artifacts_directory/upload" \
    -allowProvisioningUpdates

  printf 'Upload accepted for TestFlight: %s %s (%s), commit %s.\n' \
    "$bundle_identifier" "$archived_version" "$archived_build" "$source_commit"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
