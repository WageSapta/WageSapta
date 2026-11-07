"""Render clickable selected-project cards (wrapped in <a> tags in the README).

    python scripts/make_project_cards.py
    STATIC=1 python scripts/make_project_cards.py
"""

from common import (
    ACCENT,
    BAR_H,
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
FONT = 12.5
TITLE_FONT = 15


def build(project, width, height, static):
    narrow = width < 320
    subtitle_fs = 11 if narrow else FONT
    header = BAR_H + 28
    desc_y = header + 20
    stack_y = desc_y + 20
    keys = [("stack:", project.get("stack")), ("origin:", project.get("origin"))]

    meta = project.get("meta")
    lines = [
        f'<text x="{PAD_X}" y="{header}" font-family="{MONO}" font-size="{TITLE_FONT}" '
        f'font-weight="700" fill="{ACCENT}">{esc(project["title"])}</text>',
        (
            f'<text x="{width - PAD_X}" y="{header}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" fill="{MUTED}">{esc(meta)}</text>'
            if meta
            else ""
        ),
        f'<text x="{PAD_X}" y="{desc_y}" font-family="{MONO}" font-size="{subtitle_fs}" '
        f'fill="{FG}">{esc(project["subtitle"])}</text>',
    ]

    for key, value in keys:
        if not value:
            continue
        lines.append(
            f'<text x="{PAD_X}" y="{stack_y}" font-family="{MONO}" font-size="11" '
            f'fill="{KEY}">{esc(key)}</text>'
            f'<text x="{PAD_X + len(key) * 7.2 + 7}" y="{stack_y}" font-family="{MONO}" '
            f'font-size="11" fill="{MUTED}">{esc(value)}</text>'
        )
        stack_y += 20

    prompt = f"{project['prompt']} $ open ." if narrow else f"{project['prompt']} $ open . --in-browser"
    lines.append(
        f'<text x="{PAD_X}" y="{num(height - 12)}" font-family="{MONO}" font-size="11" '
        f'fill="{MUTED}">{esc(prompt)}</text>'
        f'<text x="{width - PAD_X}" y="{num(height - 12)}" text-anchor="end" font-family="{MONO}" '
        f'font-size="11" font-weight="700" fill="{ACCENT}">{esc("open ↗")}</text>'
    )

    style = (
        ""
        if static
        else f'<style>.card{{opacity:0;animation:print .5s ease-out forwards}}'
        f'@keyframes print{{from{{opacity:0;transform:translateY(7px)}}'
        f'to{{opacity:1;transform:translateY(0)}}}}</style>'
    )
    parts = [panel(width, height, project["label"])]
    if not static:
        parts.append(style)
    parts.append(
        f'<g class="card"{"" if static else " style=\"animation-delay:0.1s\""}>'
        + "\n".join([line for line in lines if line])
        + "</g>"
    )
    return svg(width, height, f"{project['title']} — selected project card", "\n".join(parts))


def main():
    cfg = load_config()
    static = frozen()
    for project in cfg["projects"]:
        width = float(project["width"])
        height = float(project["height"])
        path = resolve(project["output"])
        path.write_text(build(project, width, height, static), encoding="utf-8")
        print(f"wrote {project['output']} ({num(width)} x {num(height)})")


if __name__ == "__main__":
    main()
