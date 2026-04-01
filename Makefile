.PHONY: pdf svg clean fmt check

pdf:
	latexmk payments-book.tex

# Конвертировать все assets/figures/**/*.svg → .pdf для pdflatex.
# Запускать после сохранения новых Excalidraw-фигур, перед make pdf.
svg:
	python3 scripts/svg2pdf.py

clean:
	latexmk -C payments-book.tex

fmt:
	find src -name '*.tex' | xargs tex-fmt

check:
	chktex -q payments-book.tex
