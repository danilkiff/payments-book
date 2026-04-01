.PHONY: all pdf excalidraw svg clean fmt check
.DEFAULT_GOAL := all

# Полная сборка: excalidraw → svg → pdf.
all: excalidraw svg pdf

# Нормализовать label-шорткаты и конвертировать .excalidraw → .svg.
excalidraw:
	python3 scripts/label2bound.py
	python3 scripts/excalidraw2svg.py

# Конвертировать assets/figures/**/*.svg → .pdf для pdflatex.
svg:
	python3 scripts/svg2pdf.py

# Собрать книгу (требует сгенерированных figure PDF из make svg).
pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex

fmt:
	find src -name '*.tex' | xargs tex-fmt

check:
	chktex -q payments-book.tex
