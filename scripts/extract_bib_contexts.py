#!/usr/bin/env python3
"""Extract bib entries with citation contexts from .tex files.

Output: JSON Lines, one per bib entry, with fields:
  key, type, author, title, url, year, note, citations (list of {file, line, context})

Context is up to ~600 chars around the citation.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "assets" / "bibliography.bib"
SRC = ROOT / "src"


def parse_bib(text: str):
    """Yield (key, type, fields_dict) for each @entry."""
    pos = 0
    while True:
        m = re.search(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text[pos:])
        if not m:
            break
        entry_type = m.group(1).lower()
        key = m.group(2)
        start = pos + m.end()
        # find matching closing brace
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start:i-1]
        fields = parse_fields(body)
        yield key, entry_type, fields
        pos = i


def parse_fields(body: str):
    """Parse field = {value} or field = "value" pairs, returning dict."""
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        # skip whitespace and commas
        while i < n and body[i] in ", \t\n\r":
            i += 1
        if i >= n:
            break
        # read field name
        m = re.match(r"(\w+)\s*=\s*", body[i:])
        if not m:
            i += 1
            continue
        name = m.group(1).lower()
        i += m.end()
        # read value: balanced braces or quoted string
        if i < n and body[i] == "{":
            depth = 1
            i += 1
            start = i
            while i < n and depth > 0:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                if depth > 0:
                    i += 1
            value = body[start:i]
            i += 1  # past closing brace
        elif i < n and body[i] == '"':
            i += 1
            start = i
            while i < n and body[i] != '"':
                i += 1
            value = body[start:i]
            i += 1
        else:
            start = i
            while i < n and body[i] not in ",\n":
                i += 1
            value = body[start:i].strip()
        fields[name] = value.strip()
    return fields


def find_citations(key: str, tex_files):
    """Return list of {file, line, context} for each citation of key."""
    pattern = re.compile(r"\\(?:cite|footcite|textcite|parencite|cite\w*)\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}")
    hits = []
    for tf in tex_files:
        try:
            content = tf.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in pattern.finditer(content):
            keys = [k.strip() for k in m.group(1).split(",")]
            if key in keys:
                start = max(0, m.start() - 350)
                end = min(len(content), m.end() + 350)
                ctx = content[start:end]
                line = content[:m.start()].count("\n") + 1
                ctx = re.sub(r"\s+", " ", ctx).strip()
                hits.append({
                    "file": str(tf.relative_to(ROOT)),
                    "line": line,
                    "context": ctx,
                })
    return hits


def main():
    text = BIB.read_text(encoding="utf-8")
    tex_files = sorted(SRC.rglob("*.tex"))
    entries = list(parse_bib(text))
    print(f"# Parsed {len(entries)} bib entries", file=sys.stderr)
    for key, etype, fields in entries:
        citations = find_citations(key, tex_files)
        record = {
            "key": key,
            "type": etype,
            "author": fields.get("author", ""),
            "title": fields.get("title", ""),
            "url": fields.get("url", ""),
            "year": fields.get("year", ""),
            "note": fields.get("note", ""),
            "publisher": fields.get("publisher", ""),
            "journal": fields.get("journal", ""),
            "citations": citations,
        }
        print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
