BOOK = payments-book.tex
BUILD_DIR = build
BOOK_PDF = $(BUILD_DIR)/payments-book.pdf
ROOT_AUX = \
	payments-book.aux \
	payments-book.bbl \
	payments-book.bcf \
	payments-book.blg \
	payments-book.fdb_latexmk \
	payments-book.fls \
	payments-book.idx \
	payments-book.ilg \
	payments-book.ind \
	payments-book.log \
	payments-book.out \
	payments-book.run.xml \
	payments-book.synctex* \
	payments-book.toc

.PHONY: pdf clean
.DEFAULT_GOAL := pdf

pdf:
	mkdir -p $(BUILD_DIR)
	latexmk -silent -pdf -outdir=$(BUILD_DIR) $(BOOK)
	echo "[OK] Build completed: $(BOOK_PDF)"

clean:
	rm -rf $(BUILD_DIR)
	rm -f payments-book.pdf $(ROOT_AUX)
	echo "[OK] Cleanup completed"
