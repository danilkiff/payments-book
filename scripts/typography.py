#!/usr/bin/env python3
r"""
Российская типографика для LaTeX.

Применяет три правила к .tex-файлам:
  1. " --- " → "~--- " после кириллицы или знака препинания.
  2. Неразрывный пробел после в/к/с/о/у/и/а перед кириллическим словом.
     Для и/а — только если соседи короткие (≤ 8 букв).
  3. Латинские "..." вокруг кириллицы → «...».

Защищённые зоны (не трогаются):
  - math-mode: $...$, $$...$$, \( \), \[ \], окружения equation/align и т.п.
  - \texttt{...}, \lstinline{...}/\lstinline|...|, \verb|...|
  - \label{}, \ref{}, \cref{}, \Cref{}, \cite{}, \pageref{},
    \href{}, \url{}, \includegraphics{}, \input{}, \include{}
  - комментарии (хвост строки после неэкранированного %)
  - уже защищённые ~

Использование: python3 scripts/typography.py FILE [FILE ...]
"""
import re
import sys
from pathlib import Path

# --- Защищённые зоны: разбиение строки на (active, inert) куски ---

# Регулярки на однопроходные «inert» куски
_INERT_PATTERNS = [
    # math
    (r"\$\$.*?\$\$", re.DOTALL),
    (r"(?<!\\)\$.*?(?<!\\)\$", re.DOTALL),
    (r"\\\(.*?\\\)", re.DOTALL),
    (r"\\\[.*?\\\]", re.DOTALL),
    # окружения с кодом/математикой
    (r"\\begin\{(equation|equation\*|align|align\*|gather|gather\*|"
     r"multline|multline\*|verbatim|lstlisting|minted|tikzpicture)\}"
     r".*?\\end\{\1\}", re.DOTALL),
    # verb-подобные команды
    (r"\\verb\*?(.).*?\1", 0),
    (r"\\lstinline(\[[^\]]*\])?\{[^}]*\}", 0),
    (r"\\lstinline(\[[^\]]*\])?(.).*?\2", 0),
    # команды с «непрозрачными» аргументами
    (r"\\(label|ref|cref|Cref|crefrange|Crefrange|pageref|nameref|autoref|"
     r"eqref|cite|citep|citet|citeauthor|citeyear|"
     r"href|url|nolinkurl|hyperref|"
     r"includegraphics|includefiguresvg|input|include|usepackage|"
     r"documentclass|RequirePackage|providecommand|newcommand|renewcommand|"
     r"DeclareRobustCommand|newenvironment|renewenvironment|"
     r"setlength|addtolength|setcounter|addtocounter|"
     r"texttt|textsf|texttt|lstinputlisting|"
     r"bibliographystyle|bibliography|addbibresource)"
     r"(\s*\[[^\]]*\])?\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", 0),
    # texttt с возможной вложенностью на 1 уровень — сделаем отдельно ниже
]

_TEXTTT_RE = re.compile(r"\\texttt\s*\{(?:[^{}]|\{[^{}]*\})*\}")
_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)


def split_active_inert(text: str):
    """Разбивает текст на список (kind, chunk), где kind ∈ {'a','i'}.
    'a' — активная зона (правим), 'i' — инертная (не трогаем).
    """
    n = len(text)
    inert_spans = []

    # 1) собираем все защищённые диапазоны
    for pat, flags in _INERT_PATTERNS:
        for m in re.finditer(pat, text, flags):
            inert_spans.append((m.start(), m.end()))
    for m in _TEXTTT_RE.finditer(text):
        inert_spans.append((m.start(), m.end()))
    for m in _COMMENT_RE.finditer(text):
        inert_spans.append((m.start(), m.end()))

    # 2) объединяем перекрывающиеся
    inert_spans.sort()
    merged = []
    for s, e in inert_spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # 3) выдаём чередование
    out = []
    pos = 0
    for s, e in merged:
        if pos < s:
            out.append(("a", text[pos:s]))
        out.append(("i", text[s:e]))
        pos = e
    if pos < n:
        out.append(("a", text[pos:n]))
    return out


# --- Правила ---

CYR = "А-Яа-яЁё"
CYR_RE = f"[{CYR}]"

# Правило 1: em-dash. " --- " после кириллицы/знака → "~--- "
# Перед пробелом должно быть: кириллический символ или один из знаков , ; : ! ? ) ] }
# Хвост после --- : пробел, перевод строки или конец строки.
RULE_DASH_RE = re.compile(rf"(?P<pre>[{CYR},;:!?)\]\}}]) ---(?P<post>[ \t\n])")


def apply_dash(s: str) -> str:
    return RULE_DASH_RE.sub(r"\g<pre>~---\g<post>", s)


# Правило 2: неразрывный пробел после однобуквенных предлогов/союзов.
# Базовые: в, к, с, о, у — всегда.
# Союзы и, а — только если оба соседа короткие.
PREPS_ALWAYS = "вксоуВКСОУ"
PREPS_COND = "иаИА"

# «Однобуквенное слово»: предлог/союз — отдельный токен, окружённый не-буквами.
# Слева: lookbehind на не-кириллицу/латиницу (или начало строки).
# Справа: пробел, затем кириллическое слово.
LATIN = "A-Za-z"
ALPHA = CYR + LATIN

RULE_PREP_ALWAYS_RE = re.compile(
    rf"(?<![{ALPHA}])(?P<p>[{PREPS_ALWAYS}]) (?P<rest>{CYR_RE}+)"
)
RULE_PREP_COND_RE = re.compile(
    rf"(?<![{ALPHA}])(?P<p>[{PREPS_COND}]) (?P<rw>{CYR_RE}+)"
)


def apply_prep_always(s: str) -> str:
    return RULE_PREP_ALWAYS_RE.sub(r"\g<p>~\g<rest>", s)


def apply_prep_cond(s: str) -> str:
    """Союзы и/а: тильда только если контекст короткий с обеих сторон (≤ 8 букв)."""
    def repl(m: re.Match) -> str:
        i = m.start()
        rw = m.group("rw")
        # Найти левое слово: пройти назад от i-1, пропустив один разделитель (обычно пробел).
        if i == 0:
            left_word = ""
        else:
            j = i - 1
            # пропустить один пробел/перевод строки/таб
            while j >= 0 and s[j] in " \t\n":
                j -= 1
            end = j + 1
            while j >= 0 and s[j].isalpha():
                j -= 1
            left_word = s[j + 1 : end]
        if (left_word and len(left_word) > 8) or len(rw) > 8:
            return m.group(0)
        return f"{m.group('p')}~{rw}"
    return RULE_PREP_COND_RE.sub(repl, s)


# Правило 3: латинские кавычки вокруг кириллицы → «»
# "слово" → «слово»; вложенность не трогаем (редко встречается).
RULE_QUOTES_RE = re.compile(rf'"({CYR_RE}[^"]*?)"')


def apply_quotes(s: str) -> str:
    return RULE_QUOTES_RE.sub(r"«\1»", s)


# --- Pipeline ---

def transform(text: str) -> str:
    parts = split_active_inert(text)
    out = []
    for kind, chunk in parts:
        if kind == "a":
            chunk = apply_dash(chunk)
            chunk = apply_prep_always(chunk)
            chunk = apply_prep_cond(chunk)
            chunk = apply_quotes(chunk)
        out.append(chunk)
    return "".join(out)


def process_file(path: Path) -> bool:
    """Возвращает True, если файл изменился."""
    src = path.read_text(encoding="utf-8")
    dst = transform(src)
    if dst != src:
        path.write_text(dst, encoding="utf-8")
        return True
    return False


def main(argv):
    if not argv:
        print("usage: typography.py FILE [FILE ...]", file=sys.stderr)
        return 2
    changed = 0
    for arg in argv:
        p = Path(arg)
        if process_file(p):
            print(f"changed: {p}")
            changed += 1
        else:
            print(f"unchanged: {p}")
    print(f"\n{changed}/{len(argv)} files changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
