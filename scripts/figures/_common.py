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

FONT = (
  "Inter, -apple-system, BlinkMacSystemFont, "
  "'Helvetica Neue', Arial, sans-serif"
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


def _setup_path():
  """Вызывается каждым gen_*.py чтобы _common импортировался при любом cwd."""
  sys.path.insert(0, str(Path(__file__).resolve().parent))
