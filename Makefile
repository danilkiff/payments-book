.PHONY: help init pdf svg clean fmt check log
.DEFAULT_GOAL := help

help:  ## показать эту справку
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init:  ## установить git hooks (core.hooksPath → scripts/hooks)
	@git config core.hooksPath scripts/hooks
	@echo "core.hooksPath → scripts/hooks (хуки: $$(ls scripts/hooks))"

svg:  ## .svg → .pdf через Inkscape (инкрементально, по mtime)
	python3 scripts/svg2pdf.py

pdf: svg  ## собрать книгу (svg → gitversion → latexmk)
	@scripts/gen-gitversion.sh
	latexmk payments-book.tex

clean:  ## очистить build/ и удалить сгенерированные figure PDF
	latexmk -C payments-book.tex
	find assets/figures -type f -name '*.pdf' -delete

fmt:  ## форматировать .tex через tex-fmt
	find src -name '*.tex' | xargs tex-fmt

check:  ## chktex
	chktex -q payments-book.tex

log:  ## сводка warnings/errors из build/payments-book.log
	@scripts/log-summary.sh
