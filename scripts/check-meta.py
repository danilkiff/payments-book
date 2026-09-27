#!/usr/bin/env python3
"""Сверка названия, автора, DOI и ORCID в .zenodo.json, CITATION.cff,
README.md и scripts/zenodo-publish.py с src/meta.tex."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def macro(tex, name):
    value = re.search(rf"\\newcommand\{{\\{name}\}}\{{([^}}]*)\}}", tex).group(1)
    return re.sub(r"\s+", " ", value.replace("~", " ")).strip()


def main():
    tex = (ROOT / "src" / "meta.tex").read_text(encoding="utf-8")
    title, author = macro(tex, "booktitle"), macro(tex, "bookauthor")
    given, family = author.rsplit(" ", 1)
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    found = [
        (".zenodo.json title", zenodo["title"], title),
        (".zenodo.json creators", zenodo["creators"][0]["name"], f"{family}, {given}"),
    ]
    found += [
        ("CITATION.cff title", t, title)
        for t in re.findall(r'^\s*title:\s*"([^"]*)"', cff, re.M)
    ]
    found += [
        ("CITATION.cff family-names", n.strip(), family)
        for n in re.findall(r"family-names:\s*(.+)$", cff, re.M)
    ]
    found += [
        ("CITATION.cff given-names", n.strip(), given)
        for n in re.findall(r"given-names:\s*(.+)$", cff, re.M)
    ]
    doi, orcid = macro(tex, "bookdoi"), macro(tex, "bookorcid")
    found.append((".zenodo.json orcid", zenodo["creators"][0]["orcid"], orcid))
    found += [
        ("CITATION.cff doi", d, doi)
        for d in re.findall(r"^\s*(?:value|doi):\s*(10\.\S+)$", cff, re.M)
    ]
    found += [
        ("CITATION.cff orcid", o, orcid)
        for o in re.findall(r'orcid:\s*"https://orcid\.org/([^"]+)"', cff)
    ]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    found += [
        ("README.md DOI", d, doi) for d in re.findall(r"(10\.5281/zenodo\.\d+)", readme)
    ]
    publish = (ROOT / "scripts" / "zenodo-publish.py").read_text(encoding="utf-8")
    found.append(
        (
            "scripts/zenodo-publish.py CONCEPT_RECID",
            re.search(r'^CONCEPT_RECID = "(\d+)"', publish, re.M).group(1),
            doi.rsplit(".", 1)[1],
        )
    )
    errors = [f"{where}: {got!r}, в src/meta.tex {want!r}" for where, got, want in found if got != want]
    for line in errors:
        print(line, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
