#!/bin/sh

set -eu

# On macOS GUI apps often miss MacTeX in PATH. Add it opportunistically
# while preserving the normal Linux PATH-based flow.
if [ -d /Library/TeX/texbin ]; then
  PATH="/Library/TeX/texbin:$PATH"
  export PATH
fi

tool="${1:-}"
if [ -z "$tool" ]; then
  echo "usage: texlive-runner.sh <tool> [args...]" >&2
  exit 2
fi
shift

if command -v "$tool" >/dev/null 2>&1; then
  exec "$tool" "$@"
fi

echo "error: required TeX tool '$tool' was not found in PATH" >&2
echo "hint: install TeX Live/MacTeX and ensure '$tool' is available" >&2
exit 127
