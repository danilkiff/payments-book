#!/usr/bin/env python3
"""
Convert Excalidraw files: `label` shorthand → native bound-text elements.

The MCP Excalidraw tool uses a `label: {text, fontSize}` shorthand on shapes/arrows
for convenience. The Excalidraw application expects text to be stored as separate
`text` elements with `containerId` pointing to the parent.

This script normalises .excalidraw files so they render correctly in both the
Excalidraw app (labels visible) and excalidraw2svg.py.

Usage:
    python3 scripts/label2bound.py            # all assets/figures/**/*.excalidraw
    python3 scripts/label2bound.py path/to/file.excalidraw [...]
"""

import json
import sys
from pathlib import Path

# Excalidraw fontFamily 5 = Nunito (clean sans-serif, non-hand-drawn).
# Falls back gracefully to the app default in older versions.
FONT_FAMILY = 5
LINE_HEIGHT = 1.35


def _approx_text_size(text: str, font_size: float) -> tuple[float, float]:
    """Return (width, height) estimate for rendered text."""
    lines = text.split("\n")
    max_chars = max(len(l) for l in lines) if lines else 1
    w = max_chars * font_size * 0.55
    h = len(lines) * font_size * LINE_HEIGHT
    return w, h


def _make_bound_text(parent: dict, text: str, font_size: float, text_id: str) -> dict:
    px, py = parent.get("x", 0), parent.get("y", 0)
    pw, ph = parent.get("width", 0), parent.get("height", 0)
    tw, th = _approx_text_size(text, font_size)
    tw = min(tw, pw - 8)  # don't exceed container width
    tx = px + (pw - tw) / 2
    ty = py + (ph - th) / 2
    return {
        "type": "text",
        "id": text_id,
        "x": round(tx, 1),
        "y": round(ty, 1),
        "width": round(tw, 1),
        "height": round(th, 1),
        "containerId": parent["id"],
        "text": text,
        "fontSize": font_size,
        "fontFamily": FONT_FAMILY,
        "textAlign": "center",
        "verticalAlign": "middle",
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "lineHeight": LINE_HEIGHT,
    }


def convert(data: dict) -> tuple[dict, int]:
    """Return (updated_data, n_converted)."""
    elements = data.get("elements", [])
    new_elements: list[dict] = []
    n = 0

    for el in elements:
        label = el.pop("label", None)
        if not label:
            new_elements.append(el)
            continue

        text = label.get("text", "")
        font_size = float(label.get("fontSize", 16))
        if not text:
            new_elements.append(el)
            continue

        text_id = f"txt-{el['id']}"

        # Register bound element on the parent
        bound = el.setdefault("boundElements", [])
        if not any(b.get("id") == text_id for b in bound):
            bound.append({"type": "text", "id": text_id})

        new_elements.append(el)
        new_elements.append(_make_bound_text(el, text, font_size, text_id))
        n += 1

    data["elements"] = new_elements
    return data, n


def process_file(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ERROR {path.name}: {e}", file=sys.stderr)
        return 0

    data, n = convert(data)
    if n:
        path.write_text(
            json.dumps(data, ensure_ascii=False, separators=(", ", ": ")),
            encoding="utf-8",
        )
    return n


def main() -> None:
    if len(sys.argv) > 1:
        paths: list[Path] = []
        for arg in sys.argv[1:]:
            p = Path(arg)
            paths.extend(p.rglob("*.excalidraw") if p.is_dir() else [p])
    else:
        root = Path(__file__).resolve().parent.parent / "assets" / "figures"
        paths = sorted(root.rglob("*.excalidraw"))

    total = 0
    for p in paths:
        n = process_file(p)
        if n:
            print(f"  {p.name}: {n} label(s) converted")
        total += n

    print(f"Done. {total} label(s) converted across {len(paths)} file(s).")


if __name__ == "__main__":
    main()
