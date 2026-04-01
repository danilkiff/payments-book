# Authoring Guide

## Базовый подход

- Активный стек книги: `scrbook` + `pdflatex` + `latexmk` + `biblatex`.
- Приоритет — ясность исходников, а не тонкая типографская настройка.
- Новые workflow-слои и новые макросы добавлять только если без них уже трудно читать и поддерживать текст.

## Текст

Публичный author-facing набор макросов живёт в `src/commands.tex`:

`\\codeword`, `\\domain`, `\\endpoint`, `\\filepath`, `\\iso`, `\\mti`, `\\de`, `\\rc`, `\\pan`, `\\hex`, `\\law`, `\\scheme`, `\\idx`, `\\idxdef`, `\\sourcebib`.

`\\idx` и `\\idxdef` оставлены как совместимые текстовые обёртки. Они больше не строят предметный указатель.

## Сборка книги

```bash
make pdf
```

Итоговый PDF: `build/payments-book.pdf`.

Если нужно собрать напрямую:

```bash
mkdir -p build
latexmk -pdf -outdir=build payments-book.tex
```

`pdflatex` считается единственным поддерживаемым движком для основной книги. После заметных изменений в сборочном окружении или вспомогательных файлах полезно запускать `make clean`.

```bash
make clean
```

## Фигуры

- Источником правды для фигуры считается `assets/figures/<chapter>/<name>.tex`.
- `assets/figures/<chapter>/<name>.pdf` — локальный артефакт сборки. Он нужен книге, но не хранится в репозитории.
- Общий шаблон фигур в `assets/figures/templates/figure-preamble.tex` намеренно простой и совместимый с текущими исходниками.
- `make pdf` сам пересобирает figure PDF перед сборкой книги.

Если нужно пересобрать только фигуры:

```bash
make figures
```

Пример ручной пересборки фигуры:

```bash
cd assets/figures/ch07-emv
mkdir -p build
latexmk -pdf -outdir=build emv-chip-architecture.tex
cp build/emv-chip-architecture.pdf emv-chip-architecture.pdf
```

Локальный `build/` рядом с фигурой и соседний `.pdf` считаются временными артефактами. Их можно убрать через `make clean`.
