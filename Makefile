BOOK := payments-book.tex

.PHONY: pdf watch clean

pdf:
	latexmk -xelatex $(BOOK)

watch:
	latexmk -xelatex -pvc $(BOOK)

clean:
	latexmk -C $(BOOK)

.DEFAULT_GOAL := pdf
