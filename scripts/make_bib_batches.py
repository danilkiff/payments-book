#!/usr/bin/env python3
"""Split /tmp/bib_entries.jsonl into batches of N entries (with URL only).

Outputs /tmp/bib_batches/batch_NN.json — each is a JSON list of entries
ready to hand to a verification agent.
"""
import json
import os
from pathlib import Path

OUT = Path("/tmp/bib_batches")
OUT.mkdir(exist_ok=True)

# clear stale files
for f in OUT.glob("*.json"):
    f.unlink()

entries = []
with open("/tmp/bib_entries.jsonl") as f:
    for line in f:
        if line.startswith("{"):
            entries.append(json.loads(line))

with_url = [e for e in entries if e["url"]]
print(f"Entries with URL: {len(with_url)}")

BATCH = 18
batches = [with_url[i:i+BATCH] for i in range(0, len(with_url), BATCH)]
print(f"Batches of {BATCH}: {len(batches)}")

for i, b in enumerate(batches, 1):
    name = f"batch_{i:02d}.json"
    # trim contexts: keep up to 2 citations per entry, context max 400 chars
    trimmed = []
    for e in b:
        cits = e["citations"][:2]
        for c in cits:
            if len(c["context"]) > 400:
                c["context"] = c["context"][:400] + "..."
        trimmed.append({
            "key": e["key"],
            "title": e["title"],
            "url": e["url"],
            "year": e["year"],
            "note": e["note"],
            "author": e["author"],
            "citations": cits,
        })
    OUT.joinpath(name).write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  {name}: {len(b)} entries")
