# Инженерия платежей

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19884844.svg)](https://doi.org/10.5281/zenodo.19884844)

Исходники книги о карточных платежах, СБП и платёжной инфраструктуре.

```bash
# macOS
brew install mactex tex-fmt librsvg inkscape
make pdf

# Ubuntu
sudo apt install texlive-full tex-fmt librsvg2-bin inkscape  # tex-fmt: Ubuntu 25.10+
make pdf
```

## Python-примеры

Код, попадающий в книгу через `\codefile`, лежит в `samples/<глава>-<тема>/`
и проверяется тестами. Книга и тесты не расходятся по построению: в книгу
встраивается ровно тот файл, что прогоняется `pytest`.

```bash
brew install uv          # либо: curl -LsSf https://astral.sh/uv/install.sh | sh
cd samples
make sync                # установка .venv из pyproject.toml
make                     # ruff format --check + ruff check + pytest
```

`make check-code` в корне намеренно не предусмотрен: сборка PDF и
проверка python разнесены, чтобы инкрементальный билд книги не дёргал
Python-стек.

## VSCode

Открыть репо в VSCode, согласиться с расширениями из `.vscode/extensions.json`
(ms-python, Pylance, ruff, editorconfig, latex-workshop). Test Explorer
автоматически найдёт `samples/.venv` и тесты; формат при сохранении
совпадает с `make fmt`.

## Лицензия

Текст книги распространяется на условиях [CC BY-NC 4.0](LICENSE).
