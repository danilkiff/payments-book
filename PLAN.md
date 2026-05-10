# План: миграция фигур Excalidraw → Inkscape

Этап 1 (перевод пайплайна) завершён: `scripts/svg2pdf.py` рендерит через `inkscape --shell`, `excalidraw2svg.py` пишет в `*.gen.svg`, `.gitignore` коммитит Inkscape-исходники (`*.svg`), а транзиент (`*.gen.svg`) и финальный PDF — игнорирует. `librsvg` оставлен в README на переходный период.

Состояние сейчас: 68 фигур авторятся в Excalidraw как `.excalidraw`. Базнейм каждой фигуры в каждой директории должен быть представлен **либо** `.excalidraw` (легаси), **либо** `.svg` (Inkscape) — никогда оба. `svg2pdf.py` ругается на коллизию.

## Этап 2 — миграция фигур по мере правок

Триггер: правка фигуры или новая фигура. Никакого bulk-перехода: нетронутые `.excalidraw` остаются как есть.

Шаги для одной фигуры (`assets/figures/chNN-*/name.*`):

1. `python3 scripts/excalidraw2svg.py assets/figures/chNN-*/name.excalidraw` → создаёт `name.gen.svg` рядом.
2. Открыть `name.gen.svg` в Inkscape: `inkscape assets/figures/chNN-*/name.gen.svg`.
3. Сохранить как Plain SVG: File → Save As → формат «Plain SVG», имя `name.svg` (без `.gen`). Plain SVG, а не Inkscape SVG — чтобы диффы не шумели namespaced-метаданными `inkscape:` и `sodipodi:`.
4. Внести правки в Inkscape, сохранить.
5. `git rm assets/figures/chNN-*/name.excalidraw && rm assets/figures/chNN-*/name.gen.svg && git add assets/figures/chNN-*/name.svg`. Удалить `.gen.svg` обязательно: иначе `svg2pdf.py` поймает коллизию базнеймов и упадёт.
6. `make svg pdf` — проверить, что фигура рендерится.

Опционально, единоразовый помощник `scripts/migrate-figure.sh`:

```bash
#!/usr/bin/env bash
# Usage: scripts/migrate-figure.sh assets/figures/chNN-*/name.excalidraw
set -euo pipefail
src="$1"
base="${src%.excalidraw}"
python3 scripts/excalidraw2svg.py "$src"
inkscape --export-plain-svg --export-filename="${base}.svg" "${base}.gen.svg"
rm "${base}.gen.svg"
git rm "$src"
git add "${base}.svg"
echo "→ ${base}.svg готов к редактированию в Inkscape"
```

## Этап 3 — финальная очистка (когда `.excalidraw` не осталось)

Условие: `git ls-files assets/figures | grep '\.excalidraw$'` → пусто.

1. Удалить `scripts/label2bound.py` и `scripts/excalidraw2svg.py`.
2. Из `Makefile` удалить цель `excalidraw` и зависимость от неё в `all` (`all: svg pdf`).
3. Из `.gitignore` убрать строку `assets/figures/**/*.gen.svg` (не нужна — таких файлов больше не будет).
4. Из `README.md` убрать `librsvg` / `librsvg2-bin` (Inkscape остаётся единственным рендером).
5. Удалить `.PHONY` упоминание `excalidraw` в `Makefile:1`.

## Стилевая дисциплина (на любом этапе)

`excalidraw2svg.py` навязывал шрифт Inter, конкретные цвета, opacity-сплит, единый размер маркеров стрелок. После миграции фигуры в Inkscape стиль определяется руками. Чтобы новые фигуры не разъезжались:

- Создать `assets/inkscape-template.svg` с эталонной цветовой палитрой, шрифтом Inter (или другим — единым для всего корпуса), размерами стрелок, толщиной линий. Открывать его как стартовую точку для новых фигур (File → New from Template или просто Save As).
- Если Inter недоступен на CI — выбрать системный аналог (Liberation Sans / DejaVu Sans) и применить ко всему корпусу разом.

## Верификация на каждом шаге

- `make svg pdf` отрабатывает без ошибок.
- `find assets/figures -name '*.gen.svg' -newer name.svg` — для мигрированной фигуры сборка должна перезаписывать `.gen.svg` после `.svg` (на случай, если кто-то забыл удалить `.excalidraw`).
- Текст в готовом PDF — selectable (значит шрифт встроился, а не растеризовался).
- `chktex -q payments-book.tex` — без новых предупреждений.
