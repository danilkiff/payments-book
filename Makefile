.PHONY: pdf excalidraw svg clean fmt check

pdf:
	latexmk payments-book.tex

# Конвертировать assets/figures/**/*.excalidraw → .svg (чистый стиль, без hand-drawn).
# Запускать после редактирования Excalidraw-файлов, перед make svg.
excalidraw:
	python3 scripts/excalidraw2svg.py

# Конвертировать assets/figures/**/*.svg → .pdf для pdflatex.
# Полная цепочка: make excalidraw && make svg && make pdf.
svg:
	python3 scripts/svg2pdf.py

clean:
	latexmk -C payments-book.tex

fmt:
	find src -name '*.tex' | xargs tex-fmt

check:
	chktex -q payments-book.tex
