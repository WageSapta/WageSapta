"""Render a neofetch-style info card whose height matches the portrait's.

    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""

import re

from common import (
    ACCENT,
    BAR_H,
    BORDER,
    FG,
    KEY,
    MONO,
    MUTED,
    esc,
    frozen,
    load_config,
    num,
    panel,
    resolve,
    svg,
)

PAD_X = 20
FONT = 13
CHAR = FONT * 0.6
STATIC = frozen()


def portrait_height(cfg):
    """Displayed height of the portrait SVG, which becomes the card's height."""
    text = resolve(cfg["portrait"]["output"]).read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]*width="([\d.]+)" height="([\d.]+)"', text)
    w, h = float(m.group(1)), float(m.group(2))
    return h * cfg["portrait"]["display_width"] / w


def build(cfg, width, height):
    card = cfg["card"]
    rows = card["rows"]
    static = frozen()

    header = BAR_H + 26
    rule = header + 12
    first = rule + 28
    last = height - 58
    step = (last - first) / max(len(rows) - 1, 1)
    key_x = PAD_X + 78

    lines = [
        f'<text x="{PAD_X}" y="{header}" font-family="{MONO}" font-size="15" font-weight="700" '
        f'fill="{ACCENT}">{esc(card["title"])}</text>',
        f'<text x="{width - PAD_X}" y="{header}" text-anchor="end" font-family="{MONO}" '
        f'font-size="11" fill="{MUTED}">{esc(card["subtitle"])}</text>',
        f'<line x1="{PAD_X}" y1="{rule}" x2="{width - PAD_X}" y2="{rule}" stroke="{BORDER}"/>',
    ]

    for i, row in enumerate(rows):
        y = num(first + i * step)
        group = (
            f'<text x="{key_x}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{FONT}" '
            f'font-weight="700" fill="{KEY}">{esc(row["key"])}</text>'
            f'<text x="{key_x + 7}" y="{y}" font-family="{MONO}" font-size="{FONT}" '
            f'fill="{MUTED}">:</text>'
            f'<text x="{key_x + 21}" y="{y}" font-family="{MONO}" font-size="{FONT}" '
            f'fill="{FG}">{esc(row["value"])}</text>'
        )
        if static:
            lines.append(f"<g>{group}</g>")
        else:
            lines.append(f'<g class="ln" style="animation-delay:{num(0.25 + i * 0.11)}s">{group}</g>')

    prompt_x = PAD_X + len(cfg["prompt"]) * CHAR + 10
    caret_x = prompt_x + len("$ whoami") * CHAR + 4
    caret_y = height - 34
    prompt = (
        f'<text x="{PAD_X}" y="{num(height - 22)}" font-family="{MONO}" font-size="{FONT}" '
        f'fill="{ACCENT}">{esc(cfg["prompt"])}</text>'
        f'<text x="{num(prompt_x)}" y="{num(height - 22)}" font-family="{MONO}" '
        f'font-size="{FONT}" fill="{FG}">$ whoami</text>'
    )
    caret = (
        f'<rect x="{num(caret_x)}" y="{caret_y}" width="{num(CHAR)}" height="{FONT + 3}" '
        f'fill="{FG}" opacity="0.9">'
        + (
            "</rect>"
            if static
            else f'<animate attributeName="opacity" values="0.9;0.9;0;0" keyTimes="0;0.5;0.5;1" '
            f'dur="1.1s" repeatCount="indefinite"/></rect>'
        )
    )
    if static:
        lines.append(f"<g>{prompt}{caret}</g>")
    else:
        lines.append(
            f'<g class="ln" style="animation-delay:{num(0.25 + len(rows) * 0.11)}s">{prompt}{caret}</g>'
        )

    style = (
        ""
        if static
        else f'<style>.ln{{opacity:0;animation:print .5s ease-out forwards}}'
        f'@keyframes print{{from{{opacity:0;transform:translateY(7px)}}'
        f'to{{opacity:1;transform:translateY(0)}}}}</style>'
    )
    body = "\n".join([style, panel(width, height, card["label"]), "\n".join(lines)])
    return svg(width, height, f"{cfg['github_user']} profile info card", body)


def main():
    cfg = load_config()
    width = float(cfg["card"]["display_width"])
    height = portrait_height(cfg)
    resolve(cfg["card"]["output"]).write_text(build(cfg, width, height), encoding="utf-8")
    print(f"wrote {cfg['card']['output']} ({num(width)} x {num(height)})")


if __name__ == "__main__":
    main()
