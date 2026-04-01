.PHONY: pdf clean fmt check

pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex

fmt:
	find src assets/figures -name '*.tex' | xargs tex-fmt

check:
	chktex -q payments-book.tex
