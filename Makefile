.PHONY: pdf excalidraw svg clean fmt check

pdf:
	latexmk payments-book.tex

# Нормализовать label-шорткаты и конвертировать .excalidraw → .svg.
# Запускать после редактирования Excalidraw-файлов, перед make svg.
excalidraw:
	python3 scripts/label2bound.py
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
