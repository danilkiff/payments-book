.PHONY: pdf clean fmt check

pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex

fmt:
	find src assets/figures -name '*.tex' | xargs tex-fmt

check:
	chktex -q -n1 -n8 -n12 -n13 -n29 payments-book.tex
