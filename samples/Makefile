.PHONY: all check lint fmt fmt-check test sync clean
.DEFAULT_GOAL := check

# Полная проверка: формат, линт, тесты. Запускается перед коммитом примера.
check: fmt-check lint test

# Установить/обновить виртуальное окружение из pyproject.toml.
sync:
	uv sync

# Форматирование.
fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

# Линт.
lint:
	uv run ruff check .

# Тесты — рекурсивно по всем подпапкам примеров.
# Exit code 5 (no tests collected) считаем успехом — до появления первого примера.
test:
	uv run pytest; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ]

# Удалить кеши и виртуальное окружение.
clean:
	rm -rf .venv .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
