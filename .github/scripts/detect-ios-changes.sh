#!/usr/bin/env bash

set -euo pipefail

base_sha=${1:-}
head_sha=${2:-HEAD}
ios_changed=true

if [[ -n "$base_sha" && ! "$base_sha" =~ ^0+$ ]] \
  && git cat-file -e "${base_sha}^{commit}" 2>/dev/null \
  && git cat-file -e "${head_sha}^{commit}" 2>/dev/null; then
  if git diff --quiet "$base_sha" "$head_sha" -- \
    HoraAHoraApp \
    .github/workflows/ios.yml \
    .github/scripts/detect-ios-changes.sh; then
    ios_changed=false
  fi
fi

printf 'ios=%s\n' "$ios_changed" >> "${GITHUB_OUTPUT:-/dev/stdout}"
