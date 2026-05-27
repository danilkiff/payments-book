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

errors=$(count '^! ')
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
    matches=$(grep -aE "$pattern" "$LOG" 2>/dev/null | head -"$max")
    if [ -n "$matches" ]; then
        printf "\n--- %s (первые %s) ---\n%s\n" "$title" "$max" "$matches"
    fi
}

# pdflatex log смешивает UTF-8 пути с 8-битными дампами шрифтов (T2A-байты
# в Overfull-дампах не валидный UTF-8). Под LC_ALL=C awk обрабатывает
# поток как байты и не падает на multibyte conversion.
export LC_ALL=C

# Гистограмма + топ-N по ширине для Overfull \hbox.
# Бакеты: <1pt (microtype-косметика), 1-5, 5-10, 10-20, >=20pt (требует
# внимания). Файл = ближайший предшествующий push-маркер вида '(./src/.../foo.tex';
# heuristic пропускает pop-ы, но в 90\% случаев атрибуция верна.
overfull_report() {
    [ "$overfull" -eq 0 ] && return
    printf "\n--- Overfull \\hbox по ширине ---\n"
    awk '
        /^Overfull \\hbox \(/ {
            s = $0
            sub(/^Overfull \\hbox \(/, "", s)
            w = s + 0
            if      (w <  1) b1++
            else if (w <  5) b2++
            else if (w < 10) b3++
            else if (w < 20) b4++
            else             b5++
        }
        END {
            n[1]=b1+0; n[2]=b2+0; n[3]=b3+0; n[4]=b4+0; n[5]=b5+0
            lbl[1]="<1pt"; lbl[2]="1-5pt"; lbl[3]="5-10pt"
            lbl[4]="10-20pt"; lbl[5]=">=20pt"
            max=0; for (i=1;i<=5;i++) if (n[i]>max) max=n[i]
            for (i=1;i<=5;i++) {
                bar=""
                if (max>0) {
                    bl = int(n[i]*30/max)
                    for (j=0;j<bl;j++) bar = bar "█"
                }
                printf "  %-7s : %4d  %s\n", lbl[i], n[i], bar
            }
        }
    ' "$LOG"
    printf "\n--- Top-10 Overfull по ширине ---\n"
    awk '
        {
            line = $0
            while (match(line, /\(\.\/[^ )(]+\.tex/)) {
                current = substr(line, RSTART+1, RLENGTH-1)
                line = substr(line, RSTART+RLENGTH)
            }
        }
        /^Overfull \\hbox \(/ {
            s = $0
            sub(/^Overfull \\hbox \(/, "", s)
            w = s + 0
            sub(/^[0-9.]+pt too wide\) /, "", s)
            printf "%.3f\t%s\t%s\n", w, (current ? current : "?"), s
        }
    ' "$LOG" | sort -rn | head -10 | awk -F'\t' '{
        printf "  %7.2fpt  %s  %s\n", $1, $2, $3
    }'
}

# Гистограмма по badness для Underfull \hbox. badness 0-10000:
# <1k тихо, 1-3k терпимо, >5k начинает бить по глазам.
underfull_report() {
    [ "$underfull" -eq 0 ] && return
    printf "\n--- Underfull \\hbox по badness ---\n"
    awk '
        /^Underfull \\hbox \(badness [0-9]+\)/ {
            s = $0
            sub(/^Underfull \\hbox \(badness /, "", s)
            b = s + 0
            if      (b < 1000)  b1++
            else if (b < 3000)  b2++
            else if (b < 5000)  b3++
            else if (b < 10000) b4++
            else                b5++
        }
        END {
            n[1]=b1+0; n[2]=b2+0; n[3]=b3+0; n[4]=b4+0; n[5]=b5+0
            lbl[1]="<1k"; lbl[2]="1-3k"; lbl[3]="3-5k"
            lbl[4]="5-10k"; lbl[5]=">=10k"
            max=0; for (i=1;i<=5;i++) if (n[i]>max) max=n[i]
            for (i=1;i<=5;i++) {
                bar=""
                if (max>0) {
                    bl = int(n[i]*30/max)
                    for (j=0;j<bl;j++) bar = bar "█"
                }
                printf "  %-7s : %4d  %s\n", lbl[i], n[i], bar
            }
        }
    ' "$LOG"
}

show "Errors" '^! '
show "Undefined refs" 'LaTeX Warning: Reference .* undefined'
show "Undefined cites" 'LaTeX Warning: Citation .* undefined'
show "Multiply defined" 'LaTeX Warning: Label .* multiply defined'
overfull_report
underfull_report
show "Biber ERROR" '^ERROR -'
show "Biber WARN" '^WARN -'
