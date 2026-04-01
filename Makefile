BOOK := payments-book.tex
BOOK_PDF := $(BOOK:.tex=.pdf)
CLEAN_FILE_PATTERNS := \
	-name '*.aux' -o \
	-name '*.bbl' -o \
	-name '*.bcf' -o \
	-name '*.blg' -o \
	-name '*.fdb_latexmk' -o \
	-name '*.fls' -o \
	-name '*.glo' -o \
	-name '*.gls' -o \
	-name '*.idx' -o \
	-name '*.ilg' -o \
	-name '*.ind' -o \
	-name '*.lof' -o \
	-name '*.log' -o \
	-name '*.lot' -o \
	-name '*.out' -o \
	-name '*.run.xml' -o \
	-name '*.synctex' -o \
	-name '*.synctex(busy)' -o \
	-name '*.synctex.gz' -o \
	-name '*.synctex.gz(busy)' -o \
	-name '*.toc' -o \
	-name '*.xdv' -o \
	-name '*.acn' -o \
	-name '*.acr' -o \
	-name '*.alg' -o \
	-name '*.ist'

.PHONY: pdf clean

pdf:
	@latexmk -silent -xelatex $(BOOK)
	@echo "[OK] Build completed: $(BOOK_PDF)"

clean:
	@latexmk -silent -C $(BOOK)
	@find . -path './.git' -prune -o -type f \( $(CLEAN_FILE_PATTERNS) \) -exec rm -f {} +
	@rm -rf build $(BOOK_PDF)
	@echo "[OK] Cleanup completed"

.DEFAULT_GOAL := pdf
