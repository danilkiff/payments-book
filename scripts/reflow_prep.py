#!/usr/bin/env python3
"""Подготовка финальной типографской вычитки.

A) Манифест: книжная глава -> диапазон печатных страниц -> .tex -> figure-dir ->
   список SVG (с флагом generated/hand-drawn).
B) Детерминированный скан SVG против канона assets/figures/README.md:
   off-palette hex, неканоничные маркеры, fill-opacity, viewBox/aspect.
C) Скан .tex: использования \\includefiguresvg и ширина (масштаб на странице).

Пишет build/reflow-manifest.json и build/svg-canon-scan.json, печатает сводку.
Только анализ; ничего не собирает и не правит.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUX = ROOT / "build" / "payments-book.aux"
PDF = ROOT / "build" / "payments-book.pdf"
OFFSET = 2

PALETTE = {
    "#1a2030", "#5c647a", "#e8ecf7", "#f5f7fd", "#4e63d9",
    "#7759d6", "#2f8b67", "#b8821c", "#c15462", "#ffffff",
}
CANON_MARKERS = {
    "arr-accenta", "arr-accentb", "arr-good", "arr-warn", "arr-bad", "arr-muted",
    "arr-accenta-s", "arr-accentb-s", "arr-good-s", "arr-warn-s", "arr-bad-s", "arr-muted-s",
}
OK_OPACITY = {"0.15", "0.18", "0.40", "0.4"}  # 0.40 — Warn-заливка в генераторах

# Книжная глава -> часть (для дизамбигуации двойного ch13)
PART_RANGES = {1: (1, 6), 2: (7, 13), 3: (14, 24), 4: (25, 33), 5: (34, 37)}


def total_pages():
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


BACK_SLUGS = {"change-tracking", "primary-sources", "glossary", "epilogue", "colophon"}


def all_anchors():
    """Все ch:-якоря как (page, slug, is_chapter, num)."""
    pat = re.compile(r"\\newlabel\{ch:([a-z0-9-]+)\}\{\{(\d+)(?:\.\d+)?\}\{(\d+)\}")
    seen = set()
    rows = []
    for line in AUX.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        slug, num, page = m.group(1), int(m.group(2)), int(m.group(3))
        is_chapter = (1 <= num <= 37) and slug not in BACK_SLUGS
        key = (slug, page)
        if key in seen:
            continue
        seen.add(key)
        rows.append((page, slug, is_chapter, num))
    return rows


def chapter_anchors():
    out = {}
    for page, slug, is_chapter, num in all_anchors():
        if is_chapter and num not in out:
            out[num] = (slug, page)
    return out  # num -> (slug, first_page)


def part_of(num):
    for p, (lo, hi) in PART_RANGES.items():
        if lo <= num <= hi:
            return p
    return None


def resolve_tex(num):
    part = part_of(num)
    prefix = num if num <= 13 else num - 1
    cands = sorted((ROOT / "src" / "parts" / f"part{part}").glob(f"ch{prefix:02d}-*.tex"))
    # ch13 двойной: book13=one-tap(part2), book14=visa(part3) — фильтр по part уже развёл
    return cands[0] if cands else None


def gen_outputs():
    out = set()
    pat = re.compile(r'figures_dir\(\)\s*/\s*"([^"]+)"\s*/\s*"([^"]+\.svg)"')
    for g in (ROOT / "scripts" / "figures").glob("gen_*.py"):
        for m in pat.finditer(g.read_text(encoding="utf-8", errors="ignore")):
            out.add(f"{m.group(1)}/{m.group(2)}")
    return out


def scan_svg(path):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", txt)}
    off_palette = sorted(hexes - PALETTE)
    markers = {m.lower() for m in re.findall(r'id="(arr-[^"]*)"', txt)}
    off_markers = sorted(markers - CANON_MARKERS)
    used_markers = sorted(set(re.findall(r'url\(#(arr-[^)]*)\)', txt, re.I)))
    opac = sorted(set(re.findall(r'fill-opacity[:=]"?\s*([0-9.]+)', txt)))
    off_opac = [o for o in opac if o not in OK_OPACITY]
    vb = re.search(r'viewBox="([\d.\- ]+)"', txt)
    aspect = None
    vb_wh = None
    if vb:
        parts = vb.group(1).split()
        if len(parts) == 4:
            w, h = float(parts[2]), float(parts[3])
            vb_wh = [w, h]
            aspect = round(w / h, 3) if h else None
    # сколько <text> с font-size < 9
    small_fonts = sorted({s for s in re.findall(r'font-size="?([0-9.]+)', txt) if float(s) < 9})
    # пастель Excalidraw — индикатор ухода с шаблона
    excalidraw = sorted(h for h in off_palette if h in {"#b2f2bb", "#a5d8ff", "#ffec99", "#ffc9c9", "#d0bfff", "#e9ecef"})
    return {
        "off_palette": off_palette,
        "excalidraw_pastel": excalidraw,
        "off_markers": off_markers,
        "used_markers": used_markers,
        "off_opacity": off_opac,
        "all_opacity": opac,
        "viewBox": vb_wh,
        "aspect": aspect,
        "small_fonts_lt9": small_fonts,
    }


def scan_tex_includes(tex_path):
    """Найти \\includefiguresvg{path}[opts] и ширину."""
    if not tex_path or not tex_path.exists():
        return []
    txt = tex_path.read_text(encoding="utf-8", errors="ignore")
    out = []
    # \includefiguresvg[width=...]{assets/figures/.../x} ИЛИ {..}[..] — допускаем оба порядка
    for m in re.finditer(r'\\includefiguresvg(?:\[([^\]]*)\])?\{([^}]+)\}(?:\[([^\]]*)\])?', txt):
        opts = (m.group(1) or "") + (m.group(3) or "")
        wm = re.search(r'width\s*=\s*([0-9.]+)\s*\\(?:linewidth|textwidth|columnwidth)', opts)
        wabs = re.search(r'width\s*=\s*([0-9.]+)\s*(cm|mm|pt|in)', opts)
        out.append({
            "target": m.group(2),
            "opts": opts.strip(),
            "width_frac": float(wm.group(1)) if wm else None,
            "width_abs": (f"{wabs.group(1)}{wabs.group(2)}" if wabs else None),
        })
    return out


def main():
    anchors = chapter_anchors()
    tot = total_pages()
    last_printed = tot - OFFSET
    nums = sorted(anchors)
    # все граничные страницы (главы + back-matter) для точных диапазонов
    all_pages = sorted({p for p, _, _, _ in all_anchors()})
    back_pages = sorted({p for p, _, is_ch, _ in all_anchors() if not is_ch})
    ranges = {}
    for n in nums:
        first = anchors[n][1]
        nxt = next((p for p in all_pages if p > first), last_printed + 1)
        ranges[n] = (first, nxt - 1)
    front_end = anchors[nums[0]][1] - 1  # перед первой главой
    back_start = back_pages[0] if back_pages else (ranges[nums[-1]][1] + 1)

    gens = gen_outputs()
    includes_by_tex = {}
    manifest = []

    # front matter
    manifest.append({
        "key": "front-matter", "num": 0, "first_page": 1, "last_page": front_end,
        "n_pages": front_end, "tex": ["src/frontmatter/preface.tex",
        "src/frontmatter/reading-paths.tex", "src/frontmatter/toc.tex"],
        "fig_dir": None, "svgs": [],
    })

    svg_scan = {}
    for n in nums:
        first, last = ranges[n]
        tex = resolve_tex(n)
        tex_rel = str(tex.relative_to(ROOT)) if tex else None
        fig_dir = (ROOT / "assets" / "figures" / tex.stem) if tex else None
        svgs = []
        if fig_dir and fig_dir.exists():
            for svg in sorted(fig_dir.glob("*.svg")):
                rel = f"{fig_dir.name}/{svg.name}"
                is_gen = rel in gens
                sc = scan_svg(svg)
                svg_scan[rel] = {**sc, "generated": is_gen}
                svgs.append({"file": str(svg.relative_to(ROOT)), "generated": is_gen})
        incs = scan_tex_includes(tex)
        if tex_rel:
            includes_by_tex[tex_rel] = incs
        manifest.append({
            "key": f"ch{n:02d}-{anchors[n][0]}", "num": n,
            "first_page": first, "last_page": last, "n_pages": last - first + 1,
            "tex": tex_rel, "fig_dir": (str(fig_dir.relative_to(ROOT)) if fig_dir and fig_dir.exists() else None),
            "svgs": svgs,
        })

    # back matter — три блока примерно по 10 страниц
    span = last_printed - back_start + 1
    step = max(8, -(-span // 3))
    bi = 0
    p = back_start
    while p <= last_printed:
        bi += 1
        e = min(p + step - 1, last_printed)
        manifest.append({
            "key": f"back-matter-{bi}", "num": 100 + bi, "first_page": p, "last_page": e,
            "n_pages": e - p + 1, "tex": None, "fig_dir": None, "svgs": [],
        })
        p = e + 1

    (ROOT / "build" / "reflow-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "build" / "svg-canon-scan.json").write_text(
        json.dumps({"svgs": svg_scan, "includes": includes_by_tex}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    # сводка
    print(f"PDF pages={tot}  printed=1..{last_printed}  OFFSET={OFFSET}")
    print(f"units: front(1..{front_end}) + {len(nums)} chapters + back({back_start}..{last_printed})")
    bad_tex = [m for m in manifest if m["num"] and m["num"] < 100 and not m["tex"]]
    if bad_tex:
        print("!! UNRESOLVED TEX:", [m["key"] for m in bad_tex])
    print("\n== SVG canon violations ==")
    n_off = 0
    for rel, sc in sorted(svg_scan.items()):
        flags = []
        if sc["off_palette"]:
            flags.append(f"off-hex={sc['off_palette']}")
        if sc["excalidraw_pastel"]:
            flags.append(f"EXCALIDRAW={sc['excalidraw_pastel']}")
        if sc["off_markers"]:
            flags.append(f"off-markers={sc['off_markers']}")
        if sc["off_opacity"]:
            flags.append(f"opacity={sc['off_opacity']}")
        if sc["small_fonts_lt9"]:
            flags.append(f"font<9={sc['small_fonts_lt9']}")
        if flags:
            n_off += 1
            tag = "GEN" if sc["generated"] else "HAND"
            print(f"  [{tag}] {rel}: {'; '.join(flags)}")
    if not n_off:
        print("  (none — все SVG в палитре/маркерах/opacity)")

    # масштаб: ширины включений
    print("\n== \\includefiguresvg widths (масштаб на странице) ==")
    fracs = []
    for tex, incs in sorted(includes_by_tex.items()):
        for inc in incs:
            if inc["width_frac"] is not None:
                fracs.append((inc["width_frac"], inc["target"]))
            elif inc["width_abs"]:
                pass
    from collections import Counter
    c = Counter(round(f, 2) for f, _ in fracs)
    print("  width=k*\\linewidth distribution:", dict(sorted(c.items())))
    no_width = [(t, i["target"]) for t, ii in includes_by_tex.items() for i in ii
                if i["width_frac"] is None and not i["width_abs"]]
    print(f"  includes total={sum(len(v) for v in includes_by_tex.values())}, "
          f"with \\linewidth-frac={len(fracs)}, no explicit width={len(no_width)}")

    # aspect ratio разброс (намёк на «разный масштаб»)
    print("\n== viewBox aspect ratios ==")
    for rel, sc in sorted(svg_scan.items()):
        if sc["viewBox"]:
            print(f"  {sc['viewBox'][0]:.0f}x{sc['viewBox'][1]:.0f}  a={sc['aspect']}  {rel}")


if __name__ == "__main__":
    main()
