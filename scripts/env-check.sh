#!/bin/sh

set -eu

if [ -d /Library/TeX/texbin ]; then
  PATH="/Library/TeX/texbin:$PATH"
  export PATH
fi

FAIL=0

check_command() {
  name="$1"
  if path="$(command -v "$name" 2>/dev/null)"; then
    printf 'OK       %-8s %s\n' "$name" "$path"
  else
    printf 'MISSING  %-8s not found in PATH\n' "$name" >&2
    FAIL=1
  fi
}

check_command latexmk
check_command xelatex
check_command biber
check_command xindy

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/payments-book-env-check.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM

cat >"$tmpdir/font-check.tex" <<'EOF'
\documentclass{article}
\usepackage{fontspec}
\newcommand{\CheckFont}[1]{%
  \IfFontExistsTF{#1}{\typeout{FONT-OK: #1}}{\typeout{FONT-MISSING: #1}}%
}
\begin{document}
\CheckFont{PT Serif}
\CheckFont{Libertinus Serif}
\CheckFont{TeX Gyre Termes}
\CheckFont{PT Sans}
\CheckFont{Libertinus Sans}
\CheckFont{TeX Gyre Heros}
\CheckFont{PT Mono}
\CheckFont{Liberation Mono}
\CheckFont{Latin Modern Mono}
\end{document}
EOF

if ! xelatex -interaction=nonstopmode -halt-on-error -output-directory="$tmpdir" "$tmpdir/font-check.tex" >/dev/null 2>&1; then
  printf 'MISSING  fonts    font probe via xelatex failed\n' >&2
  exit 1
fi

font_log="$tmpdir/font-check.log"

has_font() {
  grep -F "FONT-OK: $1" "$font_log" >/dev/null 2>&1
}

check_font_group() {
  group="$1"
  preferred="$2"
  shift 2

  selected=""
  for font in "$preferred" "$@"; do
    if has_font "$font"; then
      selected="$font"
      break
    fi
  done

  if [ -z "$selected" ]; then
    printf 'MISSING  %-8s no usable font found\n' "$group" >&2
    FAIL=1
    return
  fi

  if [ "$selected" = "$preferred" ]; then
    printf 'OK       %-8s %s\n' "$group" "$selected"
  else
    printf 'OK       %-8s %s (fallback; preferred missing: %s)\n' "$group" "$selected" "$preferred"
  fi
}

check_font_group serif "PT Serif" "Libertinus Serif" "TeX Gyre Termes"
check_font_group sans "PT Sans" "Libertinus Sans" "TeX Gyre Heros"
check_font_group mono "PT Mono" "Liberation Mono" "Latin Modern Mono"

exit "$FAIL"
