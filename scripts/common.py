"""Shared config loading and terminal-panel SVG chrome for the profile art."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#7d8590"
KEY = "#58a6ff"
ACCENT = "#39d353"
DOTS = ("#ff5f57", "#febc2e", "#28c840")

BAR_H = 28
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"


def load_config():
    return json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))


def resolve(rel):
    return ROOT / rel


def frozen():
    return os.environ.get("STATIC") == "1"


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def num(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def svg(width, height, label, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(width)}" height="{num(height)}" '
        f'viewBox="0 0 {num(width)} {num(height)}" role="img" aria-label="{esc(label)}">\n'
        f"{body}\n</svg>\n"
    )


def panel(width, height, title, meta=None, rx=12):
    """Dark rounded window with a title bar, matching the other cards."""
    dots = "".join(
        f'<circle cx="{20 + i * 16}" cy="{num(BAR_H / 2)}" r="4.5" fill="{color}"/>'
        for i, color in enumerate(DOTS)
    )
    bar = (
        f'<path d="M0.5 {BAR_H} L0.5 {rx} Q0.5 0.5 {rx} 0.5 L{width - rx} 0.5 '
        f'Q{width - 0.5} 0.5 {width - 0.5} {rx} L{width - 0.5} {BAR_H} Z" fill="{BAR}"/>'
        f'<line x1="0.5" y1="{BAR_H}" x2="{width - 0.5}" y2="{BAR_H}" stroke="{BORDER}"/>'
    )
    meta_text = (
        ""
        if meta is None
        else f'<text x="{num(width - 14)}" y="{num(BAR_H / 2 + 4)}" text-anchor="end" '
        f'font-family="{MONO}" font-size="11" fill="{MUTED}">{esc(meta)}</text>'
    )
    return (
        f'<rect x="0.5" y="0.5" width="{num(width - 1)}" height="{num(height - 1)}" '
        f'rx="{rx}" fill="{BG}" stroke="{BORDER}"/>\n{bar}\n{dots}\n'
        f'<text x="{20 + 3 * 16 + 8}" y="{num(BAR_H / 2 + 4)}" font-family="{MONO}" '
        f'font-size="11" fill="{MUTED}">{esc(title)}</text>{meta_text}'
    )
