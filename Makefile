BOOK := payments-book.tex
LATEXMK := $(shell command -v latexmk 2>/dev/null || { test -x /Library/TeX/texbin/latexmk && echo /Library/TeX/texbin/latexmk; })

.PHONY: pdf watch clean

pdf:
	$(LATEXMK) -xelatex $(BOOK)

watch:
	$(LATEXMK) -xelatex -pvc $(BOOK)

clean:
	$(LATEXMK) -C $(BOOK)

.DEFAULT_GOAL := pdf
