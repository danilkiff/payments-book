#!/usr/bin/env python3
"""Извлечь предложения короче N слов из LaTeX-исходников и вывести в stdout."""
import argparse
import re
import sys
from pathlib import Path

MIN_LIMIT = 2
MAX_LIMIT = 20
DEFAULT_LIMIT = 10

DROP_ENVS = {
    "verbatim", "lstlisting", "minted", "tikzpicture", "tabular", "tabularx",
    "table", "table*", "figure", "figure*", "equation", "equation*",
    "align", "align*", "thebibliography", "filecontents", "filecontents*",
    "comment", "tcolorbox",
}

KEEP_CONTENT_CMDS = [
    "highlight", "emph", "textbf", "textit", "texttt", "textsc",
    "textsf", "textrm", "underline", "uline", "mbox", "hbox", "fbox",
    "framebox", "text", "mathrm", "mathit", "mathbf", "ensuremath",
    "enquote", "hl", "textsuperscript", "textsubscript",
    "caption", "importantnote", "practicenote",
]

# Commands whose two args should both be kept (joined by ". ")
KEEP_TWO_ARGS_CMDS = ["definitionnote"]


def strip_drop_envs(text: str) -> str:
    for env in DROP_ENVS:
        pat = re.compile(
            r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{" + re.escape(env) + r"\}",
            re.DOTALL,
        )
        text = pat.sub(" ", text)
    return text


def find_balanced(text: str, i: int, opener: str, closer: str):
    """Return index just past matching closer for opener at text[i], or None."""
    if i >= len(text) or text[i] != opener:
        return None
    depth = 0
    j = i
    while j < len(text):
        c = text[j]
        if c == "\\" and j + 1 < len(text):
            j += 2
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def extract_braced_arg(text: str, i: int):
    """If text[i] == '{', return (content, end_index). Else (None, i)."""
    if i >= len(text) or text[i] != "{":
        return None, i
    end = find_balanced(text, i, "{", "}")
    if end is None:
        return None, i
    return text[i + 1:end - 1], end


def skip_optional(text: str, i: int):
    """Skip [optional] argument starting at text[i], return new index."""
    if i >= len(text) or text[i] != "[":
        return i
    end = find_balanced(text, i, "[", "]")
    if end is None:
        return i
    return end


def replace_keep_cmds(text: str) -> str:
    """Replace \\cmd{X} with X for cmds in KEEP_CONTENT_CMDS, recursively."""
    pattern = re.compile(r"\\(" + "|".join(KEEP_CONTENT_CMDS) + r")\*?")
    for _ in range(8):
        out = []
        i = 0
        changed = False
        while i < len(text):
            m = pattern.match(text, i)
            if not m:
                out.append(text[i])
                i += 1
                continue
            j = m.end()
            j = skip_optional(text, j)
            arg, k = extract_braced_arg(text, j)
            if arg is None:
                out.append(text[i])
                i += 1
                continue
            out.append(" ")
            out.append(arg)
            out.append(" ")
            i = k
            changed = True
        text = "".join(out)
        if not changed:
            break
    return text


def strip_remaining_commands(text: str) -> str:
    """Strip any remaining \\cmd[opt]?{arg}* (zero or more brace args)."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n and (text[i + 1].isalpha() or text[i + 1] == "@"):
            j = i + 1
            while j < n and (text[j].isalpha() or text[j] == "@"):
                j += 1
            # optional star
            if j < n and text[j] == "*":
                j += 1
            # eat optional and brace args
            progressed = True
            while progressed:
                progressed = False
                # whitespace between cmd and args is allowed in LaTeX but rare; skip.
                while j < n and text[j] in " \t":
                    j2 = j
                    while j2 < n and text[j2] in " \t":
                        j2 += 1
                    if j2 < n and text[j2] in "[{":
                        j = j2
                        break
                    else:
                        break
                if j < n and text[j] == "[":
                    new_j = skip_optional(text, j)
                    if new_j != j:
                        j = new_j
                        progressed = True
                        continue
                if j < n and text[j] == "{":
                    end = find_balanced(text, j, "{", "}")
                    if end is not None:
                        j = end
                        progressed = True
                        continue
            out.append(" ")
            i = j
        elif c == "\\" and i + 1 < n:
            # Non-letter command like \\ \, \; \! \%
            nxt = text[i + 1]
            if nxt in "\\":
                out.append(" ")
                i += 2
            elif nxt in "%&_$#{}":
                out.append(nxt)
                i += 2
            elif nxt in ",;:! ":
                out.append(" ")
                i += 2
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_latex(text: str) -> str:
    # Remove LaTeX comments (preserve escaped \%)
    text = re.sub(r"(?<!\\)%.*", "", text)

    text = strip_drop_envs(text)

    # Drop any remaining \begin{...}/\end{...} (but keep their inner content)
    text = re.sub(r"\\begin\{[^}]*\}(\[[^\]]*\])?", " ", text)
    text = re.sub(r"\\end\{[^}]*\}", " ", text)

    # Drop \bibitem{...} markers
    text = re.sub(r"\\bibitem\{[^}]*\}", " ", text)

    # \definitionnote{title}{body} -> "title. body"
    pat2 = re.compile(r"\\(" + "|".join(KEEP_TWO_ARGS_CMDS) + r")\*?")
    for _ in range(4):
        out = []
        i = 0
        n = len(text)
        changed = False
        while i < n:
            m = pat2.match(text, i)
            if not m:
                out.append(text[i])
                i += 1
                continue
            j = m.end()
            j = skip_optional(text, j)
            a1, k1 = extract_braced_arg(text, j)
            if a1 is None:
                out.append(text[i]); i += 1; continue
            a2, k2 = extract_braced_arg(text, k1)
            if a2 is None:
                out.append(text[i]); i += 1; continue
            out.append(f" {a1}. {a2} ")
            i = k2
            changed = True
        text = "".join(out)
        if not changed:
            break

    # Replace keep-content cmds with their content
    text = replace_keep_cmds(text)

    # \href{url}{label} -> label
    text = re.sub(r"\\href\s*\{[^}]*\}\s*\{([^}]*)\}", r" \1 ", text)
    # \url{u} -> u
    text = re.sub(r"\\url\s*\{([^}]*)\}", r" \1 ", text)

    # \ldots / \dots -> ...
    text = re.sub(r"\\(?:ldots|dots)\b\{?\}?", "...", text)

    # Strip everything else
    text = strip_remaining_commands(text)

    # ~ -> space
    text = text.replace("~", " ")

    # remaining braces
    text = re.sub(r"[{}]", " ", text)

    # dashes -- and ---
    text = re.sub(r"-{2,3}", "—", text)

    return text


def split_sentences(text: str):
    paragraphs = re.split(r"\n\s*\n", text)
    sentences = []
    for p in paragraphs:
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        # Split on sentence-ending punctuation followed by space + uppercase or quote
        parts = re.split(r"(?<=[.!?…])\s+(?=[«„\"A-ZА-ЯЁ0-9])", p)
        for s in parts:
            s = s.strip()
            if s:
                sentences.append(s)
    return sentences


WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё'’\-]*|\d+")


def word_count(s: str) -> int:
    return len(WORD_RE.findall(s))


def is_meaningful(s: str) -> bool:
    """Reject leftover artifacts that aren't real prose."""
    # must contain at least one alphabetic word
    if not re.search(r"[A-Za-zА-Яа-яЁё]", s):
        return False
    # reject lines that look like option lists "[a=b, c=d]"
    if re.fullmatch(r"\[[^\]]*\]", s.strip()):
        return False
    return True


def parse_limit(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"требуется целое число, получено: {value!r}")
    if n < MIN_LIMIT or n > MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"порог должен быть в диапазоне [{MIN_LIMIT}, {MAX_LIMIT}], получено: {n}"
        )
    return n


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Извлечь предложения короче N слов из .tex-файлов в каталоге SRC. "
            "Результат пишется в stdout (Markdown)."
        )
    )
    parser.add_argument(
        "src",
        type=Path,
        help="каталог с LaTeX-исходниками (рекурсивный поиск *.tex)",
    )
    parser.add_argument(
        "limit",
        nargs="?",
        type=parse_limit,
        default=DEFAULT_LIMIT,
        help=(
            f"максимальная длина предложения в словах (строго меньше); "
            f"по умолчанию {DEFAULT_LIMIT}, допустимый диапазон [{MIN_LIMIT}, {MAX_LIMIT}]"
        ),
    )
    args = parser.parse_args(argv)

    src = args.src
    if not src.is_dir():
        parser.error(f"каталог не найден: {src}")
    limit = args.limit

    files = sorted(src.rglob("*.tex"))
    out = sys.stdout
    out.write(f"# Короткие предложения (< {limit} слов)\n\n")
    total = 0
    for f in files:
        rel = f.relative_to(src)
        try:
            raw = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        cleaned = strip_latex(raw)
        sentences = split_sentences(cleaned)
        short = []
        for s in sentences:
            wc = word_count(s)
            if 0 < wc < limit and is_meaningful(s):
                s2 = re.sub(r"\s+", " ", s).strip()
                s2 = s2.lstrip("—–-•·∙⋅ ").strip()
                # remove space before punctuation like "слово ." -> "слово."
                s2 = re.sub(r"\s+([.,;:!?…])", r"\1", s2)
                # collapse "« " and " »"
                s2 = s2.replace("« ", "«").replace(" »", "»")
                s2 = re.sub(r"\s+", " ", s2).strip()
                if s2:
                    short.append(s2)
        if not short:
            continue
        out.write(f"\n## {rel}\n\n")
        for s in short:
            out.write(f"- {s}\n")
            total += 1
    out.write(f"\n---\n\nВсего предложений: {total}\n")
    print(
        f"Порог: < {limit} слов. Записано {total} предложений.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
