#!/usr/bin/env python3
"""Export the macOS application icon from the approved master artwork.

Run on macOS. Uses system sips/iconutil; leaves other platform icons unchanged.
"""

import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root / "ui/macos/assets/app-icon.png"
output = root / "qt/installer/app/resources/anki.icns"
with tempfile.TemporaryDirectory(prefix="anki-icon-") as temporary:
    iconset = Path(temporary) / "Anki.iconset"
    iconset.mkdir()
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = size * scale
            suffix = "@2x" if scale == 2 else ""
            target = iconset / f"icon_{size}x{size}{suffix}.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(pixels),
                    str(pixels),
                    str(source),
                    "--out",
                    str(target),
                ],
                check=True,
                capture_output=True,
            )
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(output)], check=True
    )
print(output)
