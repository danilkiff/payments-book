#!/usr/bin/env bash
# Генерирует src/gitversion.tex с short SHA и датой сборки.
#
# Файл переписывается только при изменении содержимого, чтобы не дёргать
# инкрементальную пересборку latexmk без причины. Маркер +dirty добавляется,
# если рабочее дерево грязное (в CI с fresh checkout — никогда).
#
# Используется из Makefile, .github/workflows/ci.yml и release.yml.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
output="${script_dir}/../src/gitversion.tex"

sha=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    sha="${sha}+dirty"
fi
dt=$(date +%Y-%m-%d)

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '\\gdef\\bookgitsha{%s}\n\\gdef\\bookbuilddate{%s}\n' "$sha" "$dt" > "$tmp"

if ! cmp -s "$tmp" "$output" 2>/dev/null; then
    mv "$tmp" "$output"
fi
