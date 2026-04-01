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
	payments-book.log \
	payments-book.out \
	payments-book.run.xml \
	payments-book.synctex* \
	payments-book.toc

.PHONY: pdf figures clean clean-figures
.DEFAULT_GOAL := pdf

pdf: figures
	mkdir -p $(BUILD_DIR)
	latexmk -silent -pdf -outdir=$(BUILD_DIR) $(BOOK)
	echo "[OK] Build completed: $(BOOK_PDF)"

figures:
	find assets/figures -mindepth 2 -maxdepth 2 -name '*.tex' ! -path '*/templates/*' -print0 | sort -z | while IFS= read -r -d '' file; do \
		dir=$$(dirname "$$file"); \
		base=$$(basename "$$file" .tex); \
		echo "[FIG] $$file"; \
		(cd "$$dir" && mkdir -p build && latexmk -silent -pdf -outdir=build "$$base.tex" && cp "build/$$base.pdf" "$$base.pdf") || exit 1; \
	done

clean: clean-figures
	rm -rf $(BUILD_DIR)
	rm -f payments-book.pdf $(ROOT_AUX)
	echo "[OK] Cleanup completed"

clean-figures:
	find assets/figures -mindepth 2 -maxdepth 2 -name '*.tex' ! -path '*/templates/*' -print0 | while IFS= read -r -d '' file; do \
		dir=$$(dirname "$$file"); \
		base=$$(basename "$$file" .tex); \
		rm -f "$$dir/$$base.pdf"; \
		rm -rf "$$dir/build"; \
	done
