BOOK := payments-book.tex
BUILD_DIR := build
BOOK_PDF := $(BUILD_DIR)/payments-book.pdf

.PHONY: pdf clean
.DEFAULT_GOAL := pdf

pdf:
	mkdir -p $(BUILD_DIR)
	latexmk -silent -pdf -outdir=$(BUILD_DIR) $(BOOK)
	echo "[OK] Build completed: $(BOOK_PDF)"

clean:
	latexmk -silent -C -outdir=$(BUILD_DIR) $(BOOK)
	rm -rf $(BUILD_DIR) payments-book.pdf
	echo "[OK] Cleanup completed"
