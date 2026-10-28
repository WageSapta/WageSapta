"""Render the prepped portrait as a self-typing monochrome ASCII SVG.

    python scripts/make_ascii_svg.py            # writes the portrait SVG
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for local preview
"""

from PIL import Image

from common import ACCENT, BAR_H, FG, MONO, esc, frozen, load_config, num, panel, resolve, svg

RAMP = " .`:-=+*cs#%@"
CELL_ASPECT = 0.6
PAD_X = 10
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
    return img.crop(
        (
            max(0, box[0] - pad),
            max(0, box[1] - pad),
            min(w, box[2] + pad),
            min(h, box[3] + pad),
        )
    )


def metrics(cols, display_w):
    """Draw one SVG unit per rendered pixel so the window chrome is never scaled down."""
    char_w = (display_w - 2 * PAD_X) / cols
    font = char_w / CELL_ASPECT
    return char_w, font, font


def to_grid(img, cols, char_w, line_h):
    w, h = img.size
    rows = max(1, int(round(cols * (h / w) * (char_w / line_h))))
    small = img.resize((cols, rows), Image.LANCZOS)
    px = small.load()
    last = len(RAMP) - 1
    return [
        "".join(RAMP[round((255 - px[x, y]) / 255 * last)] for x in range(cols))
        for y in range(rows)
    ]


def build(lines, label, title, char_w, font, line_h):
    cols = max(len(line) for line in lines)
    grid_w = cols * char_w
    width = 2 * PAD_X + grid_w
    height = BAR_H + PAD_TOP + len(lines) * line_h + PAD_BOTTOM
    static = frozen()

    defs, rows = [], []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        begin = num(START + i * ROW_STAGGER)
        top = BAR_H + PAD_TOP + i * line_h
        clip_id = f"c{i}"
        if static:
            clip = (
                f'<clipPath id="{clip_id}"><rect x="0" y="{num(top - 1)}" width="{num(width)}" '
                f'height="{num(line_h + 2)}"/></clipPath>'
            )
        else:
            clip = (
                f'<clipPath id="{clip_id}"><rect x="0" y="{num(top - 1)}" width="0" '
                f'height="{num(line_h + 2)}"><animate attributeName="width" from="0" '
                f'to="{num(width)}" dur="{WIPE_DUR}s" begin="{begin}s" fill="freeze"/></rect></clipPath>'
            )
        defs.append(clip)
        rows.append(
            f'<g clip-path="url(#{clip_id})"><text x="{num(PAD_X)}" y="{num(top + font * 0.8)}" '
            f'xml:space="preserve" font-family="{MONO}" font-size="{num(font)}" '
            f'fill="{FG}">{esc(line)}</text></g>'
        )
        if not static:
            rows.append(
                f'<rect x="{num(PAD_X)}" y="{num(top + line_h * 0.1)}" width="{num(char_w * 1.2)}" '
                f'height="{num(line_h * 0.8)}" fill="{ACCENT}" opacity="0">'
                f'<animate attributeName="x" from="{num(PAD_X)}" to="{num(PAD_X + grid_w)}" '
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
    cols = int(portrait.get("cols", 104))
    char_w, font, line_h = metrics(cols, float(portrait.get("display_width", 370)))

    img = Image.open(resolve(portrait["source"])).convert("L")
    lines = to_grid(trim(img), cols, char_w, line_h)
    label = f"ASCII portrait of {cfg['github_user']}"
    width, height, out = build(
        lines, label, portrait.get("label", "~/portrait"), char_w, font, line_h
    )

    resolve(portrait["output"]).write_text(out, encoding="utf-8")
    print(f"wrote {portrait['output']} ({num(width)} x {num(height)}, {len(lines)} rows x {cols} cols)")


if __name__ == "__main__":
    main()
