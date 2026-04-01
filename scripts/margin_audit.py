#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


DEFAULT_LOG = Path("build/aux/main.log")
PAGE_RE = re.compile(r"Package marginnote Info: Margin note .* is on absolute page (\d+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report margin-note density using the latest LaTeX build log."
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help=f"Path to the LaTeX log file (default: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=2,
        help="Warn about pages with more than this many margin notes.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many densest pages to print.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 if any page exceeds the threshold.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.log.exists():
        print(f"Missing LaTeX log: {args.log}", file=sys.stderr)
        return 2

    counts: Counter[int] = Counter()
    for line in args.log.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = PAGE_RE.search(line)
        if match:
            counts[int(match.group(1))] += 1

    total_notes = sum(counts.values())
    total_pages = len(counts)
    offenders = sorted(
        ((page, count) for page, count in counts.items() if count > args.threshold),
        key=lambda item: (-item[1], item[0]),
    )

    print(f"Margin notes: {total_notes}")
    print(f"Pages with margin notes: {total_pages}")

    if counts:
        print("Densest pages:")
        for page, count in counts.most_common(args.limit):
            print(f"  p.{page}: {count}")
    else:
        print("Densest pages: none")

    if offenders:
        print(f"Pages above threshold ({args.threshold}):")
        for page, count in offenders[: args.limit]:
            print(f"  p.{page}: {count}")
    else:
        print(f"No pages above threshold ({args.threshold}).")

    if args.strict and offenders:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
