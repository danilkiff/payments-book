#!/usr/bin/env python3
"""
Convert .excalidraw JSON files to clean (non-hand-drawn) SVG.

Usage:
    python3 scripts/excalidraw2svg.py            # convert all assets/figures/**/*.excalidraw
    python3 scripts/excalidraw2svg.py path/to/file.excalidraw [...]
    python3 scripts/excalidraw2svg.py assets/figures/ch02-ecosystem/

Output SVG files are placed next to the .excalidraw sources (same directory, .svg extension).
They overwrite any existing .svg — run `make excalidraw` before `make svg` and `make pdf`.
"""

import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

# ── Visual constants ──────────────────────────────────────────────────────────
PADDING = 20
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
DEFAULT_STROKE = "#1e1e1e"
DEFAULT_STROKE_WIDTH = 2
LINE_HEIGHT_FACTOR = 1.35  # em-units per line


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dash(stroke_style: str) -> str:
    if stroke_style == "dashed":
        return ' stroke-dasharray="6,3"'
    if stroke_style == "dotted":
        return ' stroke-dasharray="2,3"'
    return ""


def _rx(roundness: dict | None) -> int:
    return 8 if (roundness and roundness.get("type") == 3) else 0


def _opacity_attrs(opacity: int) -> tuple[str, str]:
    """Return (fill_opacity_attr, stroke_opacity_attr) for opacity < 100.

    Excalidraw's opacity applies to the whole element. We split it into
    fill-opacity and stroke-opacity so zone backgrounds (low opacity) keep
    readable stroke borders when the element is inside a group.
    """
    if opacity >= 100:
        return "", ""
    v = opacity / 100.0
    return f' fill-opacity="{v:.2f}"', f' stroke-opacity="{v:.2f}"'


def _marker_safe_id(color: str) -> str:
    return color.lstrip("#").replace("(", "").replace(")", "").replace(",", "").replace(" ", "")


# ── Bounding-box ──────────────────────────────────────────────────────────────

def _approx_text_extents(text: str, font_size: float) -> tuple[float, float]:
    """Estimate (width, height) for rendered text in absence of explicit dims."""
    lines = (text or "").split("\n")
    max_chars = max((len(l) for l in lines), default=1)
    return max_chars * font_size * 0.55, len(lines) * font_size * LINE_HEIGHT_FACTOR


def _text_xrange(el: dict) -> tuple[float, float, float, float]:
    """Return (x_min, x_max, y_min, y_max) for a standalone text element.

    Excalidraw files authored by the MCP tool often omit width/height on text
    elements. We estimate the rendered extents and shift the bbox according to
    textAlign so right- and centre-aligned captions are not clipped from the
    left/right of the viewBox.
    """
    x = el.get("x", 0)
    y = el.get("y", 0)
    w = el.get("width") or 0
    h = el.get("height") or 0
    fs = el.get("fontSize", 16)
    text = el.get("text", "")
    tw, th = _approx_text_extents(text, fs)
    # If the file has explicit dims, trust them but fall back to estimate when 0.
    box_w = w if w else tw
    box_h = h if h else th
    align = el.get("textAlign", "left")
    if align == "center":
        if w:
            xs = (x, x + w)
        else:
            xs = (x - tw / 2, x + tw / 2)
    elif align == "right":
        if w:
            xs = (x, x + w)
        else:
            xs = (x - tw, x)
    else:  # left / unknown
        xs = (x, x + max(w, tw))
    return xs[0], xs[1], y, y + box_h


def _bbox(elements: list[dict]) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, width, height) of all drawable elements."""
    by_id = {e.get("id"): e for e in elements if e.get("id")}
    xs, ys = [], []
    for el in elements:
        t = el.get("type", "")
        if t in ("cameraUpdate", "delete", "restoreCheckpoint"):
            continue
        x, y = el.get("x", 0), el.get("y", 0)
        w, h = el.get("width", 0), el.get("height", 0)
        if t in ("arrow", "line"):
            for dx, dy in el.get("points", [[0, 0], [w, h]]):
                xs.append(x + dx)
                ys.append(y + dy)
            continue
        if t == "text":
            cid = el.get("containerId")
            if cid and cid in by_id:
                # Bound text is rendered centred on the parent container; long
                # text overflows the container box, so include estimated extents.
                p = by_id[cid]
                px, py = p.get("x", 0), p.get("y", 0)
                pw, ph = p.get("width", 0), p.get("height", 0)
                tw, th = _approx_text_extents(el.get("text", ""), el.get("fontSize", 16))
                cx, cy = px + pw / 2, py + ph / 2
                xs += [cx - tw / 2, cx + tw / 2, px, px + pw]
                ys += [cy - th / 2, cy + th / 2, py, py + ph]
            else:
                x0, x1, y0, y1 = _text_xrange(el)
                xs += [x0, x1]
                ys += [y0, y1]
            continue
        xs += [x, x + w]
        ys += [y, y + h]
    if not xs:
        return 0.0, 0.0, 800.0, 600.0
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


# ── SVG defs (markers) ────────────────────────────────────────────────────────

def _collect_arrow_colors(elements: list[dict]) -> set[str]:
    colors = set()
    for el in elements:
        if el.get("type") in ("arrow", "line"):
            c = el.get("strokeColor") or DEFAULT_STROKE
            if el.get("endArrowhead") or el.get("startArrowhead"):
                colors.add(c)
    return colors


def _defs(colors: set[str]) -> str:
    if not colors:
        return ""
    parts = ["<defs>"]
    for c in sorted(colors):
        sid = _marker_safe_id(c)
        # end arrowhead (→)
        parts.append(
            f'  <marker id="arr-{sid}" viewBox="0 0 10 10" refX="9" refY="5"'
            f' markerWidth="5" markerHeight="5" orient="auto">'
            f'<path d="M0,0 L10,5 L0,10 Z" fill="{c}"/></marker>'
        )
        # start arrowhead (←)
        parts.append(
            f'  <marker id="arr-{sid}-s" viewBox="0 0 10 10" refX="1" refY="5"'
            f' markerWidth="5" markerHeight="5" orient="auto">'
            f'<path d="M10,0 L0,5 L10,10 Z" fill="{c}"/></marker>'
        )
    parts.append("</defs>")
    return "\n".join(parts)


def _marker_end(color: str) -> str:
    return f'url(#arr-{_marker_safe_id(color)})'


def _marker_start(color: str) -> str:
    return f'url(#arr-{_marker_safe_id(color)}-s)'


# ── Text rendering ────────────────────────────────────────────────────────────

def _text_lines(
    text: str,
    cx: float,
    cy: float,
    font_size: float,
    fill: str,
    text_anchor: str = "middle",
    font_weight: str = "normal",
) -> str:
    """Render multi-line text centered at (cx, cy)."""
    lines = (text or "").split("\n")
    n = len(lines)
    lh = font_size * LINE_HEIGHT_FACTOR
    # Vertical center: first baseline offset so block is centered
    y0 = cy - (n * lh) / 2 + font_size * 0.82
    parts = []
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{cx:.1f}" y="{y0 + i * lh:.1f}"'
            f' text-anchor="{text_anchor}"'
            f' font-family="{FONT}" font-size="{font_size}" font-weight="{font_weight}"'
            f' fill="{fill}">{xml_escape(line)}</text>'
        )
    return "\n".join(parts)


def _standalone_text(el: dict, ox: float, oy: float) -> str:
    """Render a standalone `text` element."""
    x = el.get("x", 0) - ox
    y = el.get("y", 0) - oy
    w = el.get("width", 0)
    text = el.get("text", "")
    font_size = el.get("fontSize", 16)
    color = el.get("strokeColor") or DEFAULT_STROKE
    text_align = el.get("textAlign", "left")

    anchor_map = {"left": "start", "center": "middle", "right": "end"}
    anchor = anchor_map.get(text_align, "start")
    if text_align == "center":
        tx = x + w / 2 if w else x
    elif text_align == "right":
        tx = x + w if w else x
    else:
        tx = x

    lines = text.split("\n")
    lh = font_size * LINE_HEIGHT_FACTOR
    parts = []
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{tx:.1f}" y="{y + i * lh + font_size * 0.85:.1f}"'
            f' text-anchor="{anchor}"'
            f' font-family="{FONT}" font-size="{font_size}"'
            f' fill="{color}">{xml_escape(line)}</text>'
        )
    return "\n".join(parts)


# ── Shape rendering ───────────────────────────────────────────────────────────

def _shape(el: dict, ox: float, oy: float, bound_texts: dict | None = None) -> str:
    t = el.get("type")
    x = el.get("x", 0) - ox
    y = el.get("y", 0) - oy
    w = el.get("width", 0)
    h = el.get("height", 0)

    stroke = el.get("strokeColor") or DEFAULT_STROKE
    bg = el.get("backgroundColor") or "transparent"
    fill = bg if bg != "transparent" else "none"
    sw = el.get("strokeWidth", DEFAULT_STROKE_WIDTH)
    dash = _dash(el.get("strokeStyle", "solid"))
    opacity = el.get("opacity", 100)
    fo, so = _opacity_attrs(opacity)

    # Label: prefer bound text element (native Excalidraw format), fall back to
    # the `label` shorthand used by the MCP tool.
    label = el.get("label") or {}
    label_text = label.get("text", "")
    label_fs = label.get("fontSize", 16)
    label_fw = "bold" if label.get("fontWeight") == "bold" else "normal"

    bound = (bound_texts or {}).get(el.get("id", ""))
    if bound:
        label_text = bound.get("text", label_text)
        label_fs = bound.get("fontSize", label_fs)
    label_color = (bound or label).get("strokeColor") or DEFAULT_STROKE

    parts = []

    if t == "rectangle":
        rx = _rx(el.get("roundness"))
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{rx}"'
            f' fill="{fill}"{fo} stroke="{stroke}"{so} stroke-width="{sw}"{dash}/>'
        )
        if label_text:
            parts.append(_text_lines(label_text, x + w / 2, y + h / 2, label_fs, label_color,
                                     font_weight=label_fw))

    elif t == "ellipse":
        cx, cy = x + w / 2, y + h / 2
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}"'
            f' fill="{fill}"{fo} stroke="{stroke}"{so} stroke-width="{sw}"{dash}/>'
        )
        if label_text:
            parts.append(_text_lines(label_text, cx, cy, label_fs, label_color,
                                     font_weight=label_fw))

    elif t == "diamond":
        mx, my = x + w / 2, y + h / 2
        pts = f"{mx:.1f},{y:.1f} {x+w:.1f},{my:.1f} {mx:.1f},{y+h:.1f} {x:.1f},{my:.1f}"
        parts.append(
            f'<polygon points="{pts}"'
            f' fill="{fill}"{fo} stroke="{stroke}"{so} stroke-width="{sw}"{dash}/>'
        )
        if label_text:
            parts.append(_text_lines(label_text, mx, my, label_fs, label_color,
                                     font_weight=label_fw))

    return "\n".join(filter(None, parts))


# ── Arrow / Line rendering ────────────────────────────────────────────────────

def _arrow(el: dict, ox: float, oy: float, bound_texts: dict | None = None) -> str:
    t = el.get("type")
    x0 = el.get("x", 0) - ox
    y0 = el.get("y", 0) - oy
    w = el.get("width", 0)
    h = el.get("height", 0)

    color = el.get("strokeColor") or DEFAULT_STROKE
    sw = el.get("strokeWidth", DEFAULT_STROKE_WIDTH)
    dash = _dash(el.get("strokeStyle", "solid"))
    opacity = el.get("opacity", 100)
    _, so = _opacity_attrs(opacity)

    raw_pts = el.get("points") or [[0, 0], [w, h]]
    abs_pts = [(x0 + p[0], y0 + p[1]) for p in raw_pts]

    end_head = el.get("endArrowhead")
    start_head = el.get("startArrowhead")
    me = f' marker-end="{_marker_end(color)}"' if end_head and end_head != "none" else ""
    ms = f' marker-start="{_marker_start(color)}"' if start_head and start_head != "none" else ""

    parts = []

    if len(abs_pts) == 2:
        x1, y1 = abs_pts[0]
        x2, y2 = abs_pts[1]
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
            f' stroke="{color}"{so} stroke-width="{sw}"{dash}{me}{ms}/>'
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # Label offset: always above/left of midpoint.
        # For horizontal-ish arrows: shift up (−y). For vertical-ish: shift left (−x).
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1
        if abs(dx) >= abs(dy):  # mostly horizontal → label above
            lox, loy = 0.0, -10.0
        else:                   # mostly vertical → label to the left
            lox, loy = -12.0, 0.0
    else:
        # Polyline / curve — render as path
        d = "M " + " L ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in abs_pts)
        parts.append(
            f'<path d="{d}" fill="none"'
            f' stroke="{color}"{so} stroke-width="{sw}"{dash}{me}{ms}/>'
        )
        mid = len(abs_pts) // 2
        p1, p2 = abs_pts[mid - 1], abs_pts[mid]
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        lox, loy = 0.0, -10.0  # default: label above midpoint

    label = el.get("label") or {}
    label_text = label.get("text", "")
    bound = (bound_texts or {}).get(el.get("id", ""))
    if bound:
        label_text = bound.get("text", label_text)
    if label_text:
        label_fs = (bound or label).get("fontSize", 13)
        label_color = (bound or label).get("strokeColor") or color
        lx, ly = mx + lox, my + loy
        for i, line in enumerate(label_text.split("\n")):
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + i * label_fs * LINE_HEIGHT_FACTOR:.1f}"'
                f' text-anchor="middle"'
                f' font-family="{FONT}" font-size="{label_fs}"'
                f' fill="{label_color}">{xml_escape(line)}</text>'
            )

    return "\n".join(filter(None, parts))


# ── Main renderer ─────────────────────────────────────────────────────────────

def excalidraw_to_svg(data: dict) -> str:
    raw = data.get("elements", [])
    elements = [e for e in raw if e.get("type") not in
                ("cameraUpdate", "delete", "restoreCheckpoint")]

    if not elements:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>'

    # Build map: parent_id → text element (native Excalidraw bound-text format).
    # These are rendered as part of their container, not as standalone text.
    bound_texts: dict[str, dict] = {
        e["containerId"]: e
        for e in elements
        if e.get("type") == "text" and e.get("containerId")
    }
    bound_ids = {e["id"] for e in bound_texts.values()}

    min_x, min_y, total_w, total_h = _bbox(elements)
    ox = min_x - PADDING
    oy = min_y - PADDING
    vw = total_w + 2 * PADDING
    vh = total_h + 2 * PADDING

    defs = _defs(_collect_arrow_colors(elements))

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {vw:.0f} {vh:.0f}"'
        f' width="{vw:.0f}" height="{vh:.0f}">',
    ]
    if defs:
        svg_parts.append(defs)

    for el in elements:
        if el.get("id") in bound_ids:
            continue  # rendered by its container
        t = el.get("type")
        if t in ("rectangle", "ellipse", "diamond"):
            rendered = _shape(el, ox, oy, bound_texts)
        elif t in ("arrow", "line"):
            rendered = _arrow(el, ox, oy, bound_texts)
        elif t == "text":
            rendered = _standalone_text(el, ox, oy)
        else:
            continue
        if rendered:
            svg_parts.append(rendered)

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# ── File I/O ──────────────────────────────────────────────────────────────────

def convert_file(path: Path) -> Path:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ERROR {path}: invalid JSON — {e}", file=sys.stderr)
        return path.with_suffix(".svg")
    svg = excalidraw_to_svg(data)
    out = path.with_suffix(".svg")
    out.write_text(svg, encoding="utf-8")
    return out


def main() -> None:
    if len(sys.argv) > 1:
        paths: list[Path] = []
        for arg in sys.argv[1:]:
            p = Path(arg)
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.excalidraw")))
            else:
                paths.append(p)
    else:
        root = Path(__file__).resolve().parent.parent / "assets" / "figures"
        paths = sorted(root.rglob("*.excalidraw"))

    if not paths:
        print("No .excalidraw files found.")
        sys.exit(0)

    for p in paths:
        out = convert_file(p)
        try:
            rel = p.relative_to(Path(__file__).resolve().parent.parent)
        except ValueError:
            rel = p.resolve().relative_to(Path.cwd()) if p.resolve().is_relative_to(Path.cwd()) else p
        print(f"  {rel} -> {out.name}")

    print(f"Converted: {len(paths)} file(s).")


if __name__ == "__main__":
    main()
