# Helpers shared by the release scripts (deploy-testflight.sh and build-play-bundle.sh).

# Print the MARKETING_VERSION that Version.xcconfig holds at a commit.
read_marketing_version() {
  local repository_root=$1 commit=$2 version
  version=$(git -C "$repository_root" show "$commit:Version.xcconfig" 2>/dev/null \
    | sed -n 's/^MARKETING_VERSION = \(.*\)$/\1/p')
  if [[ ! "$version" =~ ^[0-9]+(\.[0-9]+){1,2}$ ]]; then
    printf 'Error: commit %s has no Version.xcconfig with a numeric MARKETING_VERSION.\n' \
      "$commit" >&2
    return 1
  fi
  printf '%s\n' "$version"
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
