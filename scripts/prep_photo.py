"""Cut a portrait out, lift local contrast and matte it onto white.

Run once per photo: `python scripts/prep_photo.py source-photo.jpg`
rembg and opencv are optional; the script degrades to alpha/auto-contrast when
they are missing.
"""

import sys
from pathlib import Path

from PIL import Image, ImageOps

from common import resolve


def remove_background(img):
    try:
        from rembg import remove
    except ImportError:
        if img.mode != "RGBA":
            print("no rembg and no alpha channel: using the photo as-is")
            return img.convert("RGB")
        return img

    print("removing background with rembg…")
    return remove(img)


def boost_contrast(img):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return ImageOps.autocontrast(img.convert("L"), cutoff=1)

    gray = img.convert("L")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    out = clahe.apply(np.asarray(gray, dtype="uint8"))
    return Image.fromarray(out)


def main(src, dst):
    img = Image.open(resolve(src) if not Path(src).is_absolute() else src)
    cut = remove_background(img)
    gray = boost_contrast(cut)

    canvas = Image.new("L", gray.size, 255)
    mask = cut.split()[-1] if cut.mode == "RGBA" else None
    canvas.paste(gray, (0, 0), mask)
    canvas.convert("RGB").save(resolve(dst))
    print(f"wrote {dst}")


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "assets/source-photo.png"
    target = sys.argv[2] if len(sys.argv) > 2 else "assets/source-prepped.png"
    main(source, target)
