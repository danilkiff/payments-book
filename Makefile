BOOK = payments-book.tex
BUILD_DIR = build
BOOK_PDF = build/payments-book.pdf

.PHONY: pdf clean
.DEFAULT_GOAL := pdf

pdf:
	mkdir -p $(BUILD_DIR)
	latexmk -silent -xelatex -outdir=$(BUILD_DIR) $(BOOK)
	echo "[OK] Build completed: $(BOOK_PDF)"

clean:
	rm -rf $(BUILD_DIR)
	rm -f payments-book.pdf
	echo "[OK] Cleanup completed"
