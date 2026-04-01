.PHONY: pdf clean

pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex
