#!/usr/bin/env python3
"""Reflow абзацев прозы по 80 видимых символов для глав книги.

Зачем: latexindent v4.0 ловит катастрофический бэктрекинг на части глав
(кириллица + \\enquote{...} + ~--- + завершающая пустая строка при
включённом removeBlockLineBreaks). Этот скрипт~--- замена-фолбэк для
таких случаев и для ручных одноразовых прогонов.

Запуск: python3 scripts/reflow.py src/parts/part3/ch18-sbp.tex [...]

Что делает:
  * собирает абзацы прозы (blank-line separated, начинаются с буквы
    или с одной из инлайн-команд: \\textbf, \\enquote, \\emph и т.д.);
  * склеивает строки внутри абзаца, заново разбивает по 80 символов;
  * сохраняет ~ как неразрывный glue (textwrap трактует через приватный
    Unicode-маркер, потом обратно);
  * не трогает: окружения tabular*, lstlisting, verbatim, equation*,
    align*, figure*, table*, tikzpicture, а также строки, начинающиеся
    с \\chapter/\\section/\\caption/\\label/\\index/\\importantnote/
    \\practicenote/\\needspace и комментарии.

После: пройти tex-fmt для нормализации индентации и chktex для линта.
"""
import sys
import re
import textwrap

WIDTH = 80
SENT = ''  # частный символ Unicode как заменитель ~ для textwrap

NO_REFLOW_ENVS = {
    'verbatim', 'lstlisting', 'minted',
    'tabular', 'tabularx', 'tabulary', 'array',
    'equation', 'equation*', 'align', 'align*', 'alignat', 'gather', 'multline',
    'figure', 'figure*', 'table', 'table*',
    'tikzpicture',
}

BEGIN_RE = re.compile(r'^\s*\\begin\{([^}]+)\}')
END_RE = re.compile(r'^\s*\\end\{([^}]+)\}')
BLOCK_END_CMD_RE = re.compile(
    r'^\s*\\(?:chapter|section|subsection|subsubsection|paragraph|subparagraph|'
    r'caption|label|index|importantnote|practicenote|needspace)\b'
)

INLINE_CMD_START = (
    '\\textbf', '\\textit', '\\emph', '\\enquote',
    '\\texttt', '\\textsc', '\\highlight',
    '\\cite', '\\ref', '\\footnote',
)


def line_starts_prose(line):
    s = line.lstrip()
    if not s:
        return False
    c = s[0]
    if c.isalpha() or c.isdigit():
        return True
    for cmd in INLINE_CMD_START:
        if s.startswith(cmd):
            return True
    return False


def wrap_paragraph(text, indent=''):
    text = text.replace('~', SENT)
    lines = textwrap.wrap(
        text, width=WIDTH,
        break_long_words=False, break_on_hyphens=False,
        initial_indent=indent, subsequent_indent=indent,
    )
    return '\n'.join(l.replace(SENT, '~') for l in lines) + '\n'


def reflow_file(path):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    block = []
    block_indent = ''
    env_stack = []

    def in_no_reflow():
        return any(e in NO_REFLOW_ENVS for e in env_stack)

    def flush():
        nonlocal block, block_indent
        if block:
            joined = ' '.join(l.strip() for l in block)
            joined = re.sub(r' +', ' ', joined)
            out.append(wrap_paragraph(joined, block_indent))
            block = []
            block_indent = ''

    for line in lines:
        stripped_nl = line.rstrip('\n')
        stripped = stripped_nl.strip()

        m_begin = BEGIN_RE.match(line)
        m_end = END_RE.match(line)

        if in_no_reflow():
            flush()
            out.append(line)
            if m_end:
                env_stack.pop()
            elif m_begin:
                env_stack.append(m_begin.group(1))
            continue

        if m_begin:
            flush()
            out.append(line)
            env_stack.append(m_begin.group(1))
            continue

        if m_end:
            flush()
            out.append(line)
            if env_stack:
                env_stack.pop()
            continue

        if not stripped:
            flush()
            out.append(line)
            continue

        if BLOCK_END_CMD_RE.match(line):
            flush()
            out.append(line)
            continue

        if stripped.startswith('%'):
            flush()
            out.append(line)
            continue

        if stripped.startswith('\\item'):
            flush()
            indent_len = len(line) - len(line.lstrip())
            block_indent = ' ' * indent_len
            block.append(stripped_nl)
            continue

        if not block:
            if line_starts_prose(line):
                indent_len = len(line) - len(line.lstrip())
                block_indent = ' ' * indent_len
                block.append(stripped_nl)
            else:
                out.append(line)
            continue

        block.append(stripped_nl)

    flush()
    return ''.join(out)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: reflow.py FILE [FILE...]', file=sys.stderr)
        sys.exit(1)
    for path in sys.argv[1:]:
        new = reflow_file(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        print(f'reflowed: {path}')
