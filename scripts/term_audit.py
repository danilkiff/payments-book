#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TERM_FILE = Path("src/preamble/terms.tex")
DEFAULT_SCAN_ROOT = Path("src/parts")

# Intentionally global abbreviations that may appear in prose without a glossary
# entry. Keep this list short and review additions carefully.
ALLOWLIST = {
    "ATM",
    "B2B",
    "B2C",
    "CBR",
    "CNP",
    "KYC",
    "MCC",
    "MDR",
    "MSC",
    "MT",
    "MX",
    "NFC",
    "PIN",
    "POS",
    "PSP",
    "URL",
    "XML",
    "ЭДС",
    "БИК",
    "НКО",
    "НСПК",
    "СБП",
    "ЦБ",
}

TOKEN_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё0-9_])([A-Z]{2,8}|[А-ЯЁ]{2,8})(?![A-Za-zА-Яа-яЁё0-9_])"
)
INTRO_TERM_RE = re.compile(r"\\(?:term|Term)(?:\[[^]]*\])?\{")
TERM_LABEL_RE = re.compile(r"\\(?:term|Term)(?:\[[^]]*\])?\{([^}]+)\}")


@dataclass
class DeclaredTerm:
    label: str
    display: str
    sort: str
    margin: str
    description: str
    line: int


@dataclass
class Paragraph:
    text: str
    start_line: int


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def read_braced_group(text: str, index: int) -> tuple[str, int]:
    index = skip_ws(text, index)
    if index >= len(text) or text[index] != "{":
        raise ValueError(f"expected '{{' at offset {index}")

    depth = 0
    start = index + 1
    cursor = index
    while cursor < len(text):
        char = text[cursor]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:cursor], cursor + 1
        cursor += 1

    raise ValueError("unterminated braced group")


def parse_declared_terms(path: Path) -> list[DeclaredTerm]:
    text = path.read_text(encoding="utf-8")
    terms: list[DeclaredTerm] = []
    matches = re.finditer(r"(?m)^[ \t]*\\DeclareTerm\b", text)

    for match in matches:
        found = match.start()
        cursor = match.end()
        args = []
        for _ in range(5):
            arg, cursor = read_braced_group(text, cursor)
            args.append(arg.strip())
        terms.append(
            DeclaredTerm(
                label=args[0],
                display=args[1],
                sort=args[2],
                margin=args[3],
                description=args[4],
                line=line_for_offset(text, found),
            )
        )

    return terms


def extract_tokens(text: str) -> set[str]:
    return {match.group(1) for match in TOKEN_RE.finditer(text)}


def iter_paragraphs(path: Path) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    chunk: list[str] = []
    start_line = 1

    for lineno, line in enumerate(lines, start=1):
        if line.strip():
            if not chunk:
                start_line = lineno
            chunk.append(line)
        elif chunk:
            paragraphs.append(Paragraph("\n".join(chunk), start_line))
            chunk = []

    if chunk:
        paragraphs.append(Paragraph("\n".join(chunk), start_line))

    return paragraphs


def default_targets() -> list[Path]:
    return sorted(path for path in DEFAULT_SCAN_ROOT.rglob("*.tex") if path.is_file())


def collect_known_tokens(terms: list[DeclaredTerm]) -> set[str]:
    known = set(ALLOWLIST)
    for term in terms:
        known.update(extract_tokens(term.display))
    return known


def collect_used_labels(paths: list[Path]) -> set[str]:
    labels: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        labels.update(TERM_LABEL_RE.findall(text))
    return labels


def short_snippet(text: str, limit: int = 120) -> str:
    flattened = " ".join(part.strip() for part in text.splitlines())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3] + "..."


def registry_findings(
    terms: list[DeclaredTerm], known_tokens: set[str], selected_labels: set[str] | None
) -> list[str]:
    findings: list[str] = []
    for term in terms:
        if selected_labels is not None and term.label not in selected_labels:
            continue
        local_known = set(known_tokens)
        local_known.update(extract_tokens(term.display))
        unresolved = sorted(
            extract_tokens(f"{term.margin} {term.description}") - local_known
        )
        for token in unresolved:
            findings.append(
                f"[registry] {TERM_FILE}:{term.line} label={term.label} depends on unresolved token {token}"
            )
    return findings


def intro_findings(paths: list[Path], known_tokens: set[str]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        for paragraph in iter_paragraphs(path):
            if not INTRO_TERM_RE.search(paragraph.text):
                continue
            labels = TERM_LABEL_RE.findall(paragraph.text)
            unresolved = sorted(extract_tokens(paragraph.text) - known_tokens)
            for token in unresolved:
                findings.append(
                    f"[intro] {path}:{paragraph.start_line} labels={','.join(labels) or '?'} unresolved token {token} | {short_snippet(paragraph.text)}"
                )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit glossary-term dependency gaps in chapter intro paragraphs and in "
            "src/preamble/terms.tex."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific .tex files or directories to scan. Defaults to src/parts.",
    )
    return parser.parse_args()


def resolve_targets(raw_paths: list[str]) -> list[Path]:
    if not raw_paths:
        return default_targets()

    targets: list[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        if path.is_dir():
            targets.extend(sorted(candidate for candidate in path.rglob("*.tex") if candidate.is_file()))
        else:
            targets.append(path)
    return targets


def main() -> int:
    args = parse_args()
    targets = resolve_targets(args.paths)

    if not TERM_FILE.exists():
        print(f"Missing term registry: {TERM_FILE}", file=sys.stderr)
        return 2

    missing = [path for path in targets if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing scan target: {path}", file=sys.stderr)
        return 2

    terms = parse_declared_terms(TERM_FILE)
    known_tokens = collect_known_tokens(terms)
    selected_labels = collect_used_labels(targets)

    findings = []
    findings.extend(registry_findings(terms, known_tokens, selected_labels))
    findings.extend(intro_findings(targets, known_tokens))

    if findings:
        print("Term audit found unresolved definition dependencies:")
        for finding in findings:
            print(f"  {finding}")
        print(
            "\nResolve each finding by registering the dependent term, spelling it "
            "out inline on first use, or rewriting the definition to avoid the "
            "unexplained acronym."
        )
        return 1

    print("Term audit passed: no unresolved dependency tokens found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
