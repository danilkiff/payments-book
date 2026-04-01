# Makefile для книги "Платёжный стек"
# Требует: latexmk, xelatex, biber

MAIN     := src/main.tex
BUILD    := build
PDF      := $(BUILD)/main.pdf

.PHONY: all pdf clean clean-all watch

## Основная сборка
all: pdf

pdf:
	latexmk -r .latexmkrc $(MAIN)
	@echo "✓  PDF: $(PDF)"

## Инкрементальная сборка с авто-перекомпиляцией при изменении файлов
watch:
	latexmk -r .latexmkrc -pvc $(MAIN)

## Удалить промежуточные файлы (оставить PDF)
clean:
	latexmk -r .latexmkrc -c $(MAIN)
	@rm -rf $(BUILD)/aux

## Удалить всё включая PDF
clean-all:
	latexmk -r .latexmkrc -C $(MAIN)
	@rm -rf $(BUILD)

## Показать список всех .tex файлов
list:
	@find src -name '*.tex' | sort

## Проверить линтером (ChkTeX)
lint:
	@find src -name '*.tex' -exec chktex -q {} \;
