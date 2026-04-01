#!/usr/bin/env bash
# Подсчёт объёма (в байтах) каждого раздела \section{} по всем главам.
# Вывод: chapter_file | section_title | bytes
#
# Использование: bash scripts/section-sizes.sh [--sort]
#   --sort  сортировать по убыванию размера

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SORT=false
[[ "${1:-}" == "--sort" ]] && SORT=true

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

for f in src/parts/part*/ch*.tex; do
  chapter=$(basename "$f" .tex)
  # Собираем номера строк \section{...} и конец файла
  lines=()
  titles=()
  while IFS=: read -r lineno text; do
    lines+=("$lineno")
    # Извлекаем заголовок из \section{...}
    title=$(echo "$text" | sed -n 's/.*\\section{\([^}]*\)}.*/\1/p')
    titles+=("$title")
  done < <(grep -n '\\section{' "$f" || true)

  total_lines=$(wc -l < "$f")

  for i in "${!lines[@]}"; do
    start=${lines[$i]}
    if (( i + 1 < ${#lines[@]} )); then
      end=$(( lines[i + 1] - 1 ))
    else
      end=$total_lines
    fi
    # Считаем байты в диапазоне строк
    bytes=$(sed -n "${start},${end}p" "$f" | wc -c | tr -d ' ')
    printf "%s\t%s\t%s\n" "$chapter" "${titles[$i]}" "$bytes"
  done
done > "$tmpfile"

if $SORT; then
  sort -t$'\t' -k3 -rn "$tmpfile"
else
  cat "$tmpfile"
fi
