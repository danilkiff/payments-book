# Authoring Guide

## Принципы

- Активный стек книги: `scrbook` + XeLaTeX + `latexmk` + `biblatex` + `imakeidx/texindy`.
- Предпочитать коробочные решения и существующие макросы, а не добавлять новые workflow-слои.
- Историю изменений и удалённых артефактов хранит система контроля версий.

## Текст

Публичный author-facing набор макросов живёт в `src/commands.tex`:

`\\codeword`, `\\domain`, `\\endpoint`, `\\filepath`, `\\iso`, `\\mti`, `\\de`, `\\rc`, `\\pan`, `\\hex`, `\\law`, `\\scheme`, `\\idx`, `\\idxdef`, `\\idxsee`, `\\idxseealso`, `\\sourcebib`.

Новые локальные макросы добавлять только если без них начинается заметное дублирование по нескольким главам.

## Сборка книги

Основной путь:

```bash
make pdf
```

Итоговый PDF:

```text
build/payments-book.pdf
```

Если нужно собрать напрямую:

```bash
mkdir -p build && latexmk -xelatex -outdir=build payments-book.tex
```

Очистка:

```bash
make clean
```

## Фигуры

- Активная техническая фигура существует как пара `assets/figures/<chapter>/<name>.tex` и `assets/figures/<chapter>/<name>.pdf`.
- Никаких manifest/status/placement-файлов у активных фигур больше нет.
- Если правится standalone-исходник фигуры, итоговый `.pdf` нужно обновить рядом с ним.

Пример ручной пересборки фигуры:

```bash
cd assets/figures/ch07-emv
mkdir -p build
latexmk -xelatex -outdir=build emv-chip-architecture.tex
cp build/emv-chip-architecture.pdf emv-chip-architecture.pdf
```

Локальный `build/` рядом с фигурой считается временным артефактом.
