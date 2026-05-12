.PHONY: help check lint fmt fmt-check test sync clean
.DEFAULT_GOAL := help

help:  ## показать эту справку
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: fmt-check lint test  ## полная проверка: формат + линт + тесты

sync:  ## установить/обновить .venv через uv
	uv sync

fmt:  ## переформатировать
	uv run ruff format .

fmt-check:  ## проверить форматирование
	uv run ruff format --check .

lint:  ## линт
	uv run ruff check .

test:  ## тесты по всем подпапкам
	uv run pytest

clean:  ## удалить .venv и кеши
	rm -rf .venv .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
