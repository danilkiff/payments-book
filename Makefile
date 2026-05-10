.PHONY: all pdf excalidraw svg clean clean-figures fmt check
.DEFAULT_GOAL := all

# Полная сборка: excalidraw → svg → pdf.
all: excalidraw svg pdf

# Нормализовать label-шорткаты и конвертировать .excalidraw → .gen.svg.
# Inkscape-исходники (*.svg) при этом не трогаются.
excalidraw:
	python3 scripts/label2bound.py
	python3 scripts/excalidraw2svg.py

# Конвертировать assets/figures/**/{*.svg,*.gen.svg} → .pdf через Inkscape.
svg:
	python3 scripts/svg2pdf.py

# Собрать книгу (требует сгенерированных figure PDF из make svg).
pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex

# Удалить генерируемые figure-артефакты (*.gen.svg и *.pdf под assets/figures/).
# Inkscape-исходники (*.svg) и .excalidraw не трогаются.
clean-figures:
	find assets/figures -type f \( -name '*.gen.svg' -o -name '*.pdf' \) -delete

fmt:
	find src -name '*.tex' | xargs tex-fmt

check:
	chktex -q payments-book.tex
