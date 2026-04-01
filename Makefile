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