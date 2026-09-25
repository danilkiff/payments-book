"""Общий модуль для генераторов SVG-фигур.

Палитра, шрифт и helper-функции едины для всех скриптов в~этом каталоге.
Source of truth для палитры -- assets/figures/README.md.

Каждый gen_*.py:
1. Импортирует константы и helpers отсюда.
2. Определяет специфические для фигуры данные (схема, пример).
3. Собирает список SVG-элементов.
4. Сохраняет через write_svg() -- путь относительно корня репозитория.

Запуск: python3 scripts/figures/gen_<name>.py из корня репозитория.
SVG падает в~assets/figures/<chapter>/<name>.svg.
Дальше make svg конвертирует SVG -> PDF через Inkscape headless.
"""
import sys
from pathlib import Path

# Палитра. Только эти цвета (+ #ffffff для негативного пространства).
# Если в~SVG появляется иной цвет -- значит, фигура ушла с~канона.
INK = "#1A2030"  # основной текст
MUTED = "#5C647A"  # вторичный текст, нейтральные стрелки
PANEL = "#E8ECF7"  # заливка панели (заметный "лист")
SOFT = "#F5F7FD"  # фон-фон, едва различимая зона
ACCENT_A = "#4E63D9"  # нейтральный смысловой акцент 1
ACCENT_B = "#7759D6"  # нейтральный смысловой акцент 2
GOOD = "#2F8B67"  # семантика "ok / разрешено / штатный путь"
WARN = "#B8821C"  # семантика "осторожно / условно / fallback"
BAD = "#C15462"  # семантика "нельзя / отказ / ошибка"

# Лестница заливок для категориальных byte-map анатомий (hex-дамп + легенда).
# Тип кодируется СВЕТЛОТОЙ, не только оттенком: при равной opacity 0.15 соседние
# каноничные оттенки (ACCENT_A vs ACCENT_B) сливаются в ΔE ~3 и исчезают при
# дальтонизме. Разнесение по тирам даёт ΔE >= 8 даже под дейтеранопией, текст
# держит контраст >= 7:1. Канон: светлый тир -> ACCENT_A, тёмный -> ACCENT_B.
TIER_PANEL = 1.0  # сплошной лист (PANEL), самый светлый тир
TIER_LIGHT = (0.22, 0.32)  # светлая пара zebra (ACCENT_A): границы соседних полей
TIER_NEUTRAL = 0.42  # нейтральный тёмный тир (MUTED)
TIER_DARK = 0.55  # тёмный тир (ACCENT_B)
TIER_LIGHT_MID = 0.27  # средняя ступень светлого тира для образца в легенде


def zebra(band, alt):
  """Ступень zebra-чередования внутри одного типа: band[1] при alt, иначе band[0].

  Размечает границу между смежными полями одного типа, не вводя нового оттенка.
  """
  return band[1] if alt else band[0]


FONT = (
  "Inter, -apple-system, BlinkMacSystemFont, "
  "'Helvetica Neue', Arial, sans-serif"
)

# Геометрия канона: 1 единица viewBox = 1 pt в~печати. Фигура включается
# \includefigure в~натуральную величину, без масштабирования.
# CANVAS_W = \textwidth (386.96 pt TeX = 385.6 bp), CANVAS_H_MAX = .45\textheight.
CANVAS_W = 385
CANVAS_H_MAX = 272

FS_HEAD = 9  # заголовок секции, bold
FS_BODY = 8  # подпись блока, подпись сообщения
FS_NOTE = 7  # пометка, подзаголовок блока; меньше нельзя

SW_FRAME = 0.5  # рамка панели, линия жизни, сетка
SW_BOX = 0.75  # контур блока
SW_LINK = 1  # связь, стрелка
DASH = "3,2"  # асинхронная, необязательная связь, ответ
RX = 3  # скругление блока

ARROW_TONES = {
  "AccentA": ACCENT_A,
  "AccentB": ACCENT_B,
  "Good": GOOD,
  "Warn": WARN,
  "Bad": BAD,
  "Muted": MUTED,
}


def markers(*tones, start=False) -> str:
  """<marker>-определения arr-<Tone> для~<defs>; без аргументов -- все шесть.

  start=True добавляет arr-<Tone>-s для~marker-start.
  """
  out = []
  for name in tones or ARROW_TONES:
    out.append(
      f'<marker id="arr-{name}" viewBox="0 0 10 10" refX="9" refY="5" '
      f'markerWidth="5" markerHeight="5" orient="auto">'
      f'<path d="M0,0 L10,5 L0,10 Z" fill="{ARROW_TONES[name]}"/></marker>'
    )
    if start:
      out.append(
        f'<marker id="arr-{name}-s" viewBox="0 0 10 10" refX="1" refY="5" '
        f'markerWidth="5" markerHeight="5" orient="auto">'
        f'<path d="M10,0 L0,5 L10,10 Z" fill="{ARROW_TONES[name]}"/></marker>'
      )
  return "".join(out)


_font_cache = {}


def _font_file(weight: str) -> str:
  import subprocess

  pattern = "Inter:bold" if weight == "bold" else "Inter:regular"
  return subprocess.run(
    ["fc-match", "-f", "%{file}", pattern],
    capture_output=True,
    text=True,
    check=True,
  ).stdout


def text_width(s: str, size=FS_BODY, weight="normal") -> float:
  """Ширина строки Inter в~pt; без файла шрифта -- оценка 0.56 em на знак."""
  key = (size, weight)
  if key not in _font_cache:
    _font_cache[key] = None
    try:
      from PIL import ImageFont

      _font_cache[key] = ImageFont.truetype(_font_file(weight), size)
    except Exception:
      pass
  font = _font_cache[key]
  if font is None:
    return 0.56 * size * len(s)
  return font.getlength(s)


def box(x, y, w, h, tone=None, dashed=False):
  """Блок канона: нейтральный (tone=None) или~с~заливкой тона 0.15 (Warn 0.18)."""
  dash = f' stroke-dasharray="{DASH}"' if dashed else ""
  if tone is None:
    return (
      f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{RX}" '
      f'fill="{PANEL}" stroke="{MUTED}" stroke-width="{SW_BOX}"{dash}/>'
    )
  color = ARROW_TONES[tone]
  op = 0.18 if tone == "Warn" else 0.15
  return (
    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{RX}" '
    f'fill="{color}" fill-opacity="{op}" stroke="{color}" '
    f'stroke-width="{SW_BOX}"{dash}/>'
  )


def arrow(x1, y1, x2, y2, tone="Muted", dashed=False):
  """Связь со~стрелкой; цвет линии и~маркера совпадают."""
  dash = f' stroke-dasharray="{DASH}"' if dashed else ""
  return (
    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    f'stroke="{ARROW_TONES[tone]}" stroke-width="{SW_LINK}"{dash} '
    f'marker-end="url(#arr-{tone})"/>'
  )


def repo_root() -> Path:
  """Корень репозитория книги."""
  return Path(__file__).resolve().parent.parent.parent


def figures_dir() -> Path:
  """assets/figures/."""
  return repo_root() / "assets" / "figures"


def xml_escape(s: str) -> str:
  """Безопасный текст для SVG-text content."""
  return (
    str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
  )


def t(x, y, s, size=10, fill=INK, weight="normal", anchor="middle"):
  """SVG <text> элемент с~единым font-family.

  Internal: символы &<> экранируются.
  Inkscape ломает PDF export на ⊕ и~подобных Unicode-операторах --
  используйте словесные эквиваленты ("XOR", "AND") в~таких случаях.
  """
  return (
    f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
    f'font-family="{FONT}" '
    f'font-size="{size}" font-weight="{weight}" '
    f'fill="{fill}">{xml_escape(s)}</text>'
  )


def write_svg(out_path: Path, lines: list) -> None:
  """Сохранить SVG. Печатает путь в~stdout."""
  out_path.parent.mkdir(parents=True, exist_ok=True)
  out_path.write_text("\n".join(lines))
  print(f"Written: {out_path.relative_to(repo_root())}")


# Преамбула для SVG: viewBox + width/height задаются вызывающим.
def svg_header(view_w: int, view_h: int, extra_defs: str = "") -> list:
  """Стандартный заголовок SVG.

  extra_defs: содержимое <defs>...</defs>, если фигуре нужны marker'ы
  или прочие defs.
  """
  out = [
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" '
    f'width="{view_w}" height="{view_h}">',
  ]
  if extra_defs:
    out.append(f"<defs>{extra_defs}</defs>")
  return out


def svg_header_pt(view_w: float, view_h: float, extra_defs: str = "") -> list:
  """Заголовок SVG канона: width/height в~pt равны viewBox."""
  out = [
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" '
    f'width="{view_w}pt" height="{view_h}pt">',
  ]
  if extra_defs:
    out.append(f"<defs>{extra_defs}</defs>")
  return out


def _setup_path():
  """Вызывается каждым gen_*.py чтобы _common импортировался при любом cwd."""
  sys.path.insert(0, str(Path(__file__).resolve().parent))
