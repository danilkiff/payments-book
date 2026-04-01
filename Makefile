# Makefile для книги "Платёжный стек"
# Требует: latexmk, xelatex, biber

MAIN     := src/main.tex
BUILD    := build
PDF      := $(BUILD)/main.pdf

.PHONY: pdf clean clean-all watch

pdf: ## Основная сборка
	latexmk -r .latexmkrc $(MAIN)
	@echo "✓  PDF: $(PDF)"

watch: ## Инкрементальная сборка с авто-перекомпиляцией при изменении файлов
	latexmk -r .latexmkrc -pvc $(MAIN)

verify: pdf ## Собрать и показать статус
	@grep 'Output written' build/aux/main.log | sed 's/.*(\([0-9]*\) pages.*/Pages: \1/'
	@printf "Errors: "; grep -c '^!' build/aux/main.log || true
	@printf "Todo items: "; grep -roc '\\todo\(fig\|cite\|check\)' src/parts/ | awk -F: '{s+=$$2} END {print s}'

clean: ## Удалить промежуточные файлы (оставить PDF)
	latexmk -r .latexmkrc -c $(MAIN)
	@rm -rf $(BUILD)/aux

clean-all: ## Удалить всё включая PDF
	latexmk -r .latexmkrc -C $(MAIN)
	@rm -rf $(BUILD)

list: ## Показать список всех .tex файлов
	@find src -name '*.tex' | sort

lint: ## Проверить линтером (ChkTeX)
	@find src -name '*.tex' -exec chktex -q {} \;

help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help