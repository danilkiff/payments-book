#!/usr/bin/env bash
# Сводка по build/payments-book.log: ошибки, undefined refs/cites, overfull,
# biber warn/err. Цель — быстро заметить регрессию в 16k строк package-info.
set -uo pipefail

LOG="${1:-build/payments-book.log}"

if [ ! -f "$LOG" ]; then
    echo "Нет файла: $LOG. Запусти make pdf." >&2
    exit 1
fi

count() { grep -cE "$1" "$LOG" 2>/dev/null || true; }

errors=$(count '^!')
undef_ref=$(count 'LaTeX Warning: Reference .* undefined')
undef_cite=$(count 'LaTeX Warning: Citation .* undefined')
multi_label=$(count 'LaTeX Warning: Label .* multiply defined')
overfull=$(count '^Overfull \\hbox')
underfull=$(count '^Underfull \\hbox')
biber_warn=$(count '^WARN -')
biber_err=$(count '^ERROR -')

printf "%-22s %s\n" "Errors (!):" "$errors"
printf "%-22s %s\n" "Undefined refs:" "$undef_ref"
printf "%-22s %s\n" "Undefined cites:" "$undef_cite"
printf "%-22s %s\n" "Multiply defined:" "$multi_label"
printf "%-22s %s\n" "Overfull \\hbox:" "$overfull"
printf "%-22s %s\n" "Underfull \\hbox:" "$underfull"
printf "%-22s %s\n" "Biber WARN:" "$biber_warn"
printf "%-22s %s\n" "Biber ERROR:" "$biber_err"

show() {
    local title="$1" pattern="$2" max="${3:-5}"
    local matches
    matches=$(grep -E "$pattern" "$LOG" 2>/dev/null | head -"$max")
    if [ -n "$matches" ]; then
        printf "\n--- %s (первые %s) ---\n%s\n" "$title" "$max" "$matches"
    fi
}

show "Errors" '^!'
show "Undefined refs" 'LaTeX Warning: Reference .* undefined'
show "Undefined cites" 'LaTeX Warning: Citation .* undefined'
show "Multiply defined" 'LaTeX Warning: Label .* multiply defined'
show "Overfull \\hbox" '^Overfull \\hbox'
show "Biber ERROR" '^ERROR -'
show "Biber WARN" '^WARN -'
