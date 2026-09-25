#!/usr/bin/env bash
# Genera les captures finals de l'App Store (1320×2868, PNG sense canal alfa)
# a partir de template.html, screens.js i les captures de raw/.
set -euo pipefail
cd "$(dirname "$0")"

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p output

ids=$(grep -o 'id: "[^"]*"' screens.js | cut -d'"' -f2)
for id in $ids; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1320,2868 \
    --virtual-time-budget=5000 --allow-file-access-from-files \
    --screenshot="output/$id.png" "file://$PWD/template.html?shot=$id" >/dev/null 2>&1
  echo "output/$id.png"
done

# App Store Connect rebutja imatges amb canal alfa: es desa en RGB pla.
uv run --quiet --with pillow python - <<'EOF'
from pathlib import Path
from PIL import Image

for path in sorted(Path("output").glob("*.png")):
    image = Image.open(path)
    assert image.size == (1320, 2868), f"{path}: {image.size}"
    image.convert("RGB").save(path, optimize=True)
EOF
