"""Render the prepped portrait as a self-typing monochrome ASCII SVG.

    python scripts/make_ascii_svg.py            # writes the portrait SVG
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for local preview
"""

import sys

from PIL import Image

from common import ACCENT, BAR_H, FG, MONO, esc, frozen, load_config, num, panel, resolve, svg

RAMP = " .`:-=+*cs#%@"
FONT_SIZE = 10.0
CHAR_W = 6.0
LINE_H = 10.0
PAD_X = 18
PAD_TOP = 16
PAD_BOTTOM = 18
ROW_STAGGER = 0.028
WIPE_DUR = 0.22
START = 0.35


def trim(img, pad_ratio=0.04):
    """Crop away the white matte so only the subject fills the grid."""
    mask = img.point(lambda p: 255 if p < 246 else 0)
    box = mask.getbbox()
    if not box:
        return img
    w, h = img.size
    pad = int(max(w, h) * pad_ratio)
    left = max(0, box[0] - pad)
    top = max(0, box[1] - pad)
    right = min(w, box[2] + pad)
    bottom = min(h, box[3] + pad)
    return img.crop((left, top, right, bottom))


def to_grid(img, cols):
    w, h = img.size
    rows = max(1, int(round(cols * (h / w) * (CHAR_W / LINE_H))))
    small = img.resize((cols, rows), Image.LANCZOS)
    px = small.load()
    last = len(RAMP) - 1
    return [
        "".join(RAMP[round((255 - px[x, y]) / 255 * last)] for x in range(cols))
        for y in range(rows)
    ]


def build(lines, label, title):
    cols = max(len(line) for line in lines)
    grid_w = cols * CHAR_W
    width = 2 * PAD_X + grid_w
    height = BAR_H + PAD_TOP + len(lines) * LINE_H + PAD_BOTTOM
    static = frozen()

    defs, rows = [], []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        begin = num(START + i * ROW_STAGGER)
        top = BAR_H + PAD_TOP + i * LINE_H
        clip_id = f"c{i}"
        if static:
            clip = f'<clipPath id="{clip_id}"><rect x="0" y="{num(top - 1)}" width="{num(width)}" height="{num(LINE_H + 2)}"/></clipPath>'
        else:
            clip = (
                f'<clipPath id="{clip_id}"><rect x="0" y="{num(top - 1)}" width="0" '
                f'height="{num(LINE_H + 2)}"><animate attributeName="width" from="0" '
                f'to="{num(width)}" dur="{WIPE_DUR}s" begin="{begin}s" fill="freeze"/></rect></clipPath>'
            )
        defs.append(clip)
        rows.append(
            f'<g clip-path="url(#{clip_id})"><text x="{PAD_X}" y="{num(top + FONT_SIZE * 0.8)}" '
            f'xml:space="preserve" font-family="{MONO}" font-size="{num(FONT_SIZE)}" '
            f'fill="{FG}">{esc(line)}</text></g>'
        )
        if not static:
            rows.append(
                f'<rect x="{PAD_X}" y="{num(top + 1)}" width="{num(CHAR_W * 1.2)}" '
                f'height="{num(LINE_H * 0.8)}" fill="{ACCENT}" opacity="0">'
                f'<animate attributeName="x" from="{PAD_X}" to="{num(PAD_X + grid_w)}" '
                f'dur="{WIPE_DUR}s" begin="{begin}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0;0.85;0.85;0" '
                f'keyTimes="0;0.05;0.85;1" dur="{num(WIPE_DUR + 0.12)}s" begin="{begin}s" '
                f'fill="freeze"/></rect>'
            )

    body = "\n".join(
        ["<defs>" + "".join(defs) + "</defs>", panel(width, height, title), "\n".join(rows)]
    )
    return width, height, svg(width, height, label, body)


def main():
    cfg = load_config()
    portrait = cfg["portrait"]
    img = Image.open(resolve(portrait["source"])).convert("L")
    lines = to_grid(trim(img), int(portrait.get("cols", 104)))
    label = f"ASCII portrait of {cfg['github_user']}"
    width, height, out = build(lines, label, portrait.get("label", "~/portrait"))
    resolve(portrait["output"]).write_text(out, encoding="utf-8")
    print(f"wrote {portrait['output']} ({len(lines)} rows x {max(len(l) for l in lines)} cols)")
    print(f"README width={portrait.get('display_width', 370)} -> height={num(height * portrait.get('display_width', 370) / width)}")


if __name__ == "__main__":
    main()
