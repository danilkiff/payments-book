#!/bin/bash
# Сериализованная обёртка над `make all`.
#
# Зачем: фикс-агенты иногда запускают несколько `make all` параллельно (через
# Bash run_in_background или последовательные тулколы без ожидания), latexmk
# и biber пишут в общие aux/bcf — гонка ломает сборку.
#
# Решение: atomic-mkdir lock. Второй вызов ждёт первого до TIMEOUT секунд.
# Никогда не запускай через `run_in_background: true`. Только синхронно.
set -euo pipefail

LOCK_DIR="/tmp/payments-book-make.lock"
TIMEOUT="${BUILD_LOCK_TIMEOUT:-900}"  # 15 минут максимум
START=$(date +%s)
WAITED=0

while ! mkdir "$LOCK_DIR" 2>/dev/null; do
  NOW=$(date +%s)
  ELAPSED=$(( NOW - START ))
  if (( ELAPSED > TIMEOUT )); then
    echo "build.sh: lock timeout ($TIMEOUT s) — кто-то держит $LOCK_DIR" >&2
    exit 124
  fi
  if (( WAITED == 0 )); then
    echo "build.sh: ждём lock $LOCK_DIR (PID-владельца не пишем — mkdir atomic) ..."
    WAITED=1
  fi
  sleep 2
done

trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

# По умолчанию полная сборка. Принимаем переопределение через первый аргумент:
#   ./scripts/build.sh         → make all
#   ./scripts/build.sh pdf     → make pdf  (без regen svg, быстрее)
TARGET="${1:-all}"
# Запускаем make как child (не exec) — иначе EXIT trap не сработает
# и lock-dir останется после сборки, блокируя следующие вызовы.
make "$TARGET"

