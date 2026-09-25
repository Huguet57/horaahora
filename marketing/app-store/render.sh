#!/usr/bin/env bash
# Genera les captures finals de l'App Store (PNG sense canal alfa) a partir de
# template.html, screens.js i les captures de raw/:
#   output/6.9/  1320×2868, apartat «iPhone 6,9"» d'App Store Connect;
#   output/6.5/  1284×2778, apartat «iPhone 6,5"».
set -euo pipefail
cd "$(dirname "$0")"

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
rm -rf output
mkdir -p output/6.9 output/6.5

ids=$(grep -o 'id: "[^"]*"' screens.js | cut -d'"' -f2)
for id in $ids; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1320,2868 \
    --virtual-time-budget=5000 --allow-file-access-from-files \
    --screenshot="output/6.9/$id.png" "file://$PWD/template.html?shot=$id" >/dev/null 2>&1
done

# La versió de 6,5" és la mateixa composició escalada sense deformar-la; els
# 12 px que sobren per baix es retallen, on el mòbil ja surt del marc.
# App Store Connect rebutja imatges amb canal alfa: es desa tot en RGB pla.
uv run --quiet --with pillow python - <<'EOF'
from pathlib import Path
from PIL import Image

for path in sorted(Path("output/6.9").glob("*.png")):
    image = Image.open(path).convert("RGB")
    assert image.size == (1320, 2868), f"{path}: {image.size}"
    image.save(path, optimize=True)

    width, height = 1284, 2778
    scaled = image.resize((width, round(2868 * width / 1320)), Image.LANCZOS)
    scaled.crop((0, 0, width, height)).save(Path("output/6.5") / path.name, optimize=True)
    print(path, "i", Path("output/6.5") / path.name)
EOF
