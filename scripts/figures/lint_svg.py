#!/usr/bin/env python3
"""Проверка SVG-фигур на~канон assets/figures/README.md.

Фигура канона -- корневой <svg> с~width/height в~pt. Фигура без pt --
legacy: печатается в~сводке и~роняет проверку только с~--strict.

  python3 scripts/figures/lint_svg.py [--strict] [файлы.svg ...]
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ARROW_TONES, CANVAS_H_MAX, CANVAS_W, DASH, FS_BODY, FS_HEAD, FS_NOTE, INK,
  MUTED, PANEL, SOFT, SW_BOX, SW_FRAME, SW_LINK, figures_dir, repo_root,
  text_width,
)

PALETTE = {c.upper() for c in (*ARROW_TONES.values(), INK, MUTED, PANEL, SOFT)}
PALETTE.add("#FFFFFF")
FONT_SIZES = {FS_NOTE, FS_BODY, FS_HEAD}
STROKES = {SW_FRAME, SW_BOX, SW_LINK}
OPACITIES = {0.15, 0.18, 0.22, 0.27, 0.32, 0.42, 0.55, 1}
MARKERS = {f"arr-{n}" for n in ARROW_TONES} | {f"arr-{n}-s" for n in ARROW_TONES}
FORBIDDEN_CHARS = "⊕⊗"
SVG_NS = "{http://www.w3.org/2000/svg}"


def _num(v):
  return float(re.sub(r"(px|pt)$", "", v.strip()))


def _props(el):
  """Атрибуты представления элемента с~учётом style="a:b;...". """
  props = dict(el.attrib)
  for part in props.pop("style", "").split(";"):
    if ":" in part:
      k, v = part.split(":", 1)
      props[k.strip()] = v.strip()
  return props


def lint(path: Path) -> tuple[bool, list[str]]:
  """(canon, ошибки). canon=False -- legacy-фигура, ошибки не~собираются."""
  root = ET.parse(path).getroot()
  width, height = root.get("width", ""), root.get("height", "")
  if not width.endswith("pt"):
    return False, []
  errs = []
  vb = [float(x) for x in root.get("viewBox", "0 0 0 0").split()]
  vw, vh = vb[2], vb[3]
  if (_num(width), _num(height)) != (vw, vh):
    errs.append(f"width/height {width}x{height} не равны viewBox {vw:g}x{vh:g}")
  if vw > CANVAS_W:
    errs.append(f"ширина {vw:g} > {CANVAS_W}")
  if vh > CANVAS_H_MAX:
    errs.append(f"высота {vh:g} > {CANVAS_H_MAX}: делить фигуру")

  text = path.read_text()
  for c in sorted({c.upper() for c in re.findall(r"#[0-9a-fA-F]{6}\b", text)} - PALETTE):
    errs.append(f"цвет {c} вне палитры")
  if re.search(r"\b(sodipodi|inkscape):", text):
    errs.append("атрибуты sodipodi:/inkscape:, сохранять как Plain SVG")
  for ch in FORBIDDEN_CHARS:
    if ch in text:
      errs.append(f"символ {ch}: Inkscape ломает PDF, писать словом")

  def walk(el, ctx):
    p = _props(el)
    ctx = {**ctx, **{k: p[k] for k in ("font-size", "font-weight", "text-anchor") if k in p}}
    tag = el.tag.replace(SVG_NS, "")
    if tag == "marker" and el.get("id") not in MARKERS:
      errs.append(f"маркер {el.get('id')} вне канона arr-<Tone>")
    if "font-family" in p and not p["font-family"].lstrip("'\"").startswith("Inter"):
      errs.append(f"шрифт {p['font-family'][:30]} вместо Inter")
    if "font-size" in p and _num(p["font-size"]) not in FONT_SIZES:
      errs.append(f"кегль {p['font-size']} вне {sorted(FONT_SIZES)}")
    if tag not in ("marker", "path") or el.get("stroke"):
      if "stroke-width" in p and _num(p["stroke-width"]) not in STROKES:
        errs.append(f"толщина {p['stroke-width']} вне {sorted(STROKES)}")
    if "stroke-dasharray" in p and p["stroke-dasharray"].replace(" ", "") != DASH:
      errs.append(f"пунктир {p['stroke-dasharray']} вместо {DASH}")
    if "fill-opacity" in p and round(float(p["fill-opacity"]), 2) not in OPACITIES:
      errs.append(f"fill-opacity {p['fill-opacity']} вне канона")
    if p.get("stroke", "").upper() == INK.upper():
      errs.append("обводка Ink: Ink только для текста")
    if tag == "text":
      s = "".join(el.itertext())
      size = _num(ctx.get("font-size", str(FS_BODY)))
      weight = "bold" if ctx.get("font-weight") in ("bold", "700") else "normal"
      w = text_width(s, size, weight)
      x = float(el.get("x", "0").split()[0])
      anchor = ctx.get("text-anchor", "start")
      left = {"start": x, "middle": x - w / 2, "end": x - w}.get(anchor, x)
      if left < -0.5 or left + w > vw + 0.5:
        errs.append(f"текст {s[:30]!r} выходит за холст")
    for child in el:
      walk(child, ctx)

  walk(root, {})
  return True, errs


def main(argv):
  strict = "--strict" in argv
  args = [a for a in argv if a != "--strict"]
  files = [Path(a) for a in args] or sorted(figures_dir().rglob("*.svg"))
  files = [f for f in files if f.suffix == ".svg" and f.exists()]
  failed, legacy = 0, []
  for f in files:
    rel = f.resolve().relative_to(repo_root())
    canon, errs = lint(f)
    if not canon:
      legacy.append(rel)
      continue
    for e in dict.fromkeys(errs):
      print(f"{rel}: {e}")
    failed += bool(errs)
  if legacy:
    print(f"legacy (вне канона, к миграции): {len(legacy)}", file=sys.stderr)
    if strict:
      for rel in legacy:
        print(f"  {rel}", file=sys.stderr)
  return 1 if failed or (strict and legacy) else 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
