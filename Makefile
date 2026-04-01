.PHONY: pdf clean fmt

pdf:
	latexmk payments-book.tex

clean:
	latexmk -C payments-book.tex

fmt:
	find src assets/figures -name '*.tex' | xargs tex-fmt
