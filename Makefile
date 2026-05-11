.PHONY: all pdf excalidraw svg clean clean-figures fmt check FORCE
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
pdf: src/gitversion.tex
	latexmk payments-book.tex

# Версия экземпляра для колофона: short SHA + дата сборки + маркер «грязного» дерева.
# Файл переписывается только при изменении содержимого, чтобы не дёргать инкрементальную
# пересборку latexmk без причины. Зависимость от FORCE — чтобы рецепт запускался каждый раз.
src/gitversion.tex: FORCE
	@sha=$$(git rev-parse --short HEAD 2>/dev/null || echo unknown); \
	 if [ -n "$$(git status --porcelain 2>/dev/null)" ]; then sha=$${sha}+dirty; fi; \
	 dt=$$(date +%Y-%m-%d); \
	 tmp=$$(mktemp); \
	 printf '\\gdef\\bookgitsha{%s}\n\\gdef\\bookbuilddate{%s}\n' "$$sha" "$$dt" > $$tmp; \
	 if ! cmp -s $$tmp $@ 2>/dev/null; then mv $$tmp $@; else rm $$tmp; fi

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
