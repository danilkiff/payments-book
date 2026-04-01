#!/usr/bin/env python3

import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


COLUMNS = 120
NO_WRAP_ENVS = {
    "verbatim",
    "verbatim*",
    "lstlisting",
    "minted",
    "tikzpicture",
    "equation",
    "equation*",
    "align",
    "align*",
    "alignat",
    "alignat*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "tabular",
    "tabular*",
    "longtable",
    "array",
    "matrix",
    "pmatrix",
    "bmatrix",
    "vmatrix",
    "Vmatrix",
    "cases",
}
STRUCTURAL_COMMANDS = {
    "appendix",
    "backmatter",
    "bibliography",
    "begin",
    "caption",
    "centering",
    "chapter",
    "chapter*",
    "frontmatter",
    "include",
    "includegraphics",
    "input",
    "item",
    "label",
    "mainmatter",
    "marginnote",
    "end",
    "paragraph",
    "paragraph*",
    "part",
    "part*",
    "printbibliography",
    "printglossary",
    "printindex",
    "section",
    "section*",
    "sidecaption",
    "subparagraph",
    "subparagraph*",
    "subsection",
    "subsection*",
    "subsubsection",
    "subsubsection*",
    "tableofcontents",
}
BEGIN_RE = re.compile(r"^\s*\\begin\{([^}]+)\}")
END_RE = re.compile(r"^\s*\\end\{([^}]+)\}")
COMMAND_RE = re.compile(r"^\s*\\([A-Za-z@*]+)")


def find_latexindent() -> str:
    candidates = []
    latexindent = shutil.which("latexindent")
    if latexindent:
        candidates.append(latexindent)
    candidates.extend(
        [
            "/opt/homebrew/bin/latexindent",
            "/usr/local/bin/latexindent",
            "/Library/TeX/texbin/latexindent",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    print("error: latexindent was not found in PATH", file=sys.stderr)
    sys.exit(127)


def has_unescaped_percent(line: str) -> bool:
    escaped = False
    for char in line:
        if char == "\\":
            escaped = not escaped
            continue
        if char == "%" and not escaped:
            return True
        escaped = False
    return False


def is_wrappable_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("%"):
        return False
    if "\\\\" in stripped:
        return False
    if has_unescaped_percent(line):
        return False
    command = COMMAND_RE.match(line)
    if not command:
        return True
    return command.group(1) not in STRUCTURAL_COMMANDS


def wrap_paragraph(lines: list[str]) -> list[str]:
    if not lines:
        return []
    indent_width = min(len(line) - len(line.lstrip(" \t")) for line in lines if line.strip())
    indent = " " * indent_width
    text = " ".join(line.strip() for line in lines)
    width = max(COLUMNS - indent_width, 20)
    wrapped = textwrap.fill(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [indent + part if part else "" for part in wrapped.splitlines()]


def reflow_text(text: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    no_wrap_stack: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.extend(wrap_paragraph(paragraph))
            paragraph = []

    for line in text.splitlines():
        begin = BEGIN_RE.match(line)
        end = END_RE.match(line)

        if end and no_wrap_stack and no_wrap_stack[-1] == end.group(1):
            flush_paragraph()
            output.append(line)
            no_wrap_stack.pop()
            continue

        if no_wrap_stack:
            output.append(line)
            continue

        if begin and begin.group(1) in NO_WRAP_ENVS:
            flush_paragraph()
            output.append(line)
            no_wrap_stack.append(begin.group(1))
            continue

        if not line.strip():
            flush_paragraph()
            output.append(line)
            continue

        if is_wrappable_line(line):
            paragraph.append(line)
            continue

        flush_paragraph()
        output.append(line)

    flush_paragraph()
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    latexindent = find_latexindent()
    proc = subprocess.run(
        [latexindent, *sys.argv[1:]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.stderr:
        sys.stderr.buffer.write(proc.stderr)
    if proc.returncode != 0:
        return proc.returncode
    formatted = proc.stdout.decode("utf-8")
    sys.stdout.write(reflow_text(formatted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
