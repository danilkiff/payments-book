.PHONY: help init all pdf svg clean clean-figures fmt check FORCE
.DEFAULT_GOAL := help

help:  ## показать эту справку
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init:  ## установить git hooks (core.hooksPath → scripts/hooks)
	@git config core.hooksPath scripts/hooks
	@echo "core.hooksPath → scripts/hooks (хуки: $$(ls scripts/hooks))"

all: svg pdf  ## полная сборка: svg → pdf

svg:  ## .svg → .pdf через Inkscape
	python3 scripts/svg2pdf.py

pdf: src/gitversion.tex  ## собрать книгу (нужны figure PDF из make svg)
	latexmk payments-book.tex

# Версия экземпляра для разворота: short SHA + дата сборки + маркер «грязного» дерева.
# Файл переписывается только при изменении содержимого, чтобы не дёргать инкрементальную
# пересборку latexmk без причины. Зависимость от FORCE — чтобы рецепт запускался каждый раз.
src/gitversion.tex: FORCE
	@sha=$$(git rev-parse --short HEAD 2>/dev/null || echo unknown); \
	 if [ -n "$$(git status --porcelain 2>/dev/null)" ]; then sha=$${sha}+dirty; fi; \
	 dt=$$(date +%Y-%m-%d); \
	 tmp=$$(mktemp); \
	 printf '\\gdef\\bookgitsha{%s}\n\\gdef\\bookbuilddate{%s}\n' "$$sha" "$$dt" > $$tmp; \
	 if ! cmp -s $$tmp $@ 2>/dev/null; then mv $$tmp $@; else rm $$tmp; fi

clean:  ## latexmk -C (очистить build/)
	latexmk -C payments-book.tex

clean-figures:  ## удалить *.pdf под assets/figures/ (перерендерятся через make svg)
	find assets/figures -type f -name '*.pdf' -delete

fmt:  ## форматировать .tex через tex-fmt
	find src -name '*.tex' | xargs tex-fmt

check:  ## chktex
	chktex -q payments-book.tex
