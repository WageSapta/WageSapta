"""Render data/contributions.json as an animated 53-week heatmap SVG.

    python scripts/render_heatmap_svg.py
    STATIC=1 python scripts/render_heatmap_svg.py
"""

import json
from datetime import datetime

from common import BAR_H, FG, MONO, MUTED, esc, frozen, load_config, num, panel, resolve, svg

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

PAD_X = 20
GUTTER = 26
BOX = 12
PITCH = 15
GRID_TOP_OFF = 40
LEGEND_OFF = 22
STATS_OFF = 44
START = 0.2
WEEK_STAGGER = 0.028
DAY_STAGGER = 0.05


def iso(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


def layout(days):
    """Bucket days into GitHub's Sun-first week columns."""
    first = iso(days[0]["date"])
    origin = first.toordinal() - (first.weekday() + 1) % 7
    weeks, months = 0, {}
    cells = []
    for day in days:
        d = iso(day["date"])
        col = (d.toordinal() - origin) // 7
        row = (d.weekday() + 1) % 7
        weeks = max(weeks, col + 1)
        cells.append({**day, "col": col, "row": row})
        months.setdefault(col, d.strftime("%b"))
    return cells, weeks, months


def month_labels(months, weeks, grid_x, y, max_x):
    out, last = [], -9
    for col in range(weeks):
        name = months.get(col)
        if not name or col - last < 5:
            continue
        x = grid_x + col * PITCH
        if x + 26 > max_x:
            continue
        last = col
        out.append(
            f'<text x="{num(x)}" y="{y}" font-family="{MONO}" font-size="10" '
            f'fill="{MUTED}">{esc(name)}</text>'
        )
    return out


def build(cfg, data):
    heat = cfg["heatmap"]
    width = float(heat.get("width", 860))
    cells, weeks, months = layout(data["days"])
    grid_x = PAD_X + GUTTER
    grid_y = BAR_H + GRID_TOP_OFF
    grid_bottom = grid_y + 6 * PITCH + BOX
    legend_y = grid_bottom + LEGEND_OFF
    stats_y = grid_bottom + STATS_OFF
    height = stats_y + 16

    static = frozen()
    best = data["stats"].get("best") or {}
    best_date = best.get("date")

    parts = []
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{num(grid_x - 8)}" y="{num(grid_y + row * PITCH + 9)}" text-anchor="end" '
            f'font-family="{MONO}" font-size="10" fill="{MUTED}">{name}</text>'
        )
    parts += month_labels(months, weeks, grid_x, num(grid_y - 10), width - PAD_X)

    for cell in cells:
        x = grid_x + cell["col"] * PITCH
        y = grid_y + cell["row"] * PITCH
        color = PALETTE[min(cell["level"], 4)]
        if best_date and cell["date"] == best_date:
            color = PALETTE[5]
        delay = num(START + cell["col"] * WEEK_STAGGER + cell["row"] * DAY_STAGGER)
        attrs = "" if static else f' class="cell" style="animation-delay:{delay}s"'
        parts.append(
            f'<rect{attrs} x="{num(x)}" y="{num(y)}" width="{BOX}" height="{BOX}" rx="2.5" '
            f'fill="{color}"/>'
        )

    lx = width - PAD_X - (5 * 14 + 60)
    parts.append(
        f'<text x="{num(lx - 8)}" y="{legend_y}" text-anchor="end" font-family="{MONO}" '
        f'font-size="10" fill="{MUTED}">Less</text>'
    )
    for i in range(5):
        parts.append(
            f'<rect x="{num(lx + i * 14)}" y="{num(legend_y - 9)}" width="{BOX}" height="{BOX}" '
            f'rx="2.5" fill="{PALETTE[i]}"/>'
        )
    parts.append(
        f'<text x="{num(lx + 5 * 14 + 6)}" y="{legend_y}" font-family="{MONO}" font-size="10" '
        f'fill="{MUTED}">More</text>'
    )

    stats = data["stats"]
    streak = (
        f'current streak {stats["current"]}d'
        if stats["current"]
        else f'last active {iso(stats["last_active"]).strftime("%d %b")}'
    )
    footer = (
        f'{data["total"]:,} contributions in the last year'
        f'   ·   {streak}'
        f'   ·   longest {stats["longest"]}d'
    )
    if best:
        d = iso(best["date"]).strftime("%d %b")
        footer += f'   ·   best day {best["count"]} on {d}'
    parts.append(
        f'<text x="{num(grid_x)}" y="{num(stats_y)}" '
        f'font-family="{MONO}" font-size="11" fill="{FG}">{esc(footer)}</text>'
    )
    style = (
        ""
        if static
        else f'<style>.cell{{transform-box:fill-box;opacity:0;animation:drop .5s ease-out forwards}}'
        f'@keyframes drop{{from{{opacity:0;transform:translateY(-9px)}}'
        f'to{{opacity:1;transform:translateY(0)}}}}</style>'
    )
    body = "\n".join(
        [style, panel(width, height, heat["label"], f'updated {data["fetched_at"]}'), "\n".join(parts)]
    )
    return svg(width, height, f"Contribution heatmap for {cfg['github_user']}", body)


def main():
    cfg = load_config()
    data = json.loads(resolve(cfg["heatmap"]["data"]).read_text(encoding="utf-8"))
    out = build(cfg, data)
    resolve(cfg["heatmap"]["output"]).write_text(out, encoding="utf-8")
    print(f"wrote {cfg['heatmap']['output']} ({data['total']:,} contributions)")


if __name__ == "__main__":
    main()
