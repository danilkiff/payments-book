#!/usr/bin/env python3
"""Публикация PDF новой версией записи Zenodo.

  ZENODO_TOKEN=... python3 scripts/zenodo-publish.py PDF VERSION

Метаданные берутся из .zenodo.json, version и publication_date
подставляются. Повторный запуск подхватывает незавершённый черновик.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("ZENODO_API", "https://zenodo.org/api")
CONCEPT_RECID = "19884844"
ROOT = Path(__file__).resolve().parent.parent


def call(method, url, data=None, content_type="application/json"):
  headers = {"Authorization": f"Bearer {os.environ['ZENODO_TOKEN']}"}
  if data is not None:
    headers["Content-Type"] = content_type
  req = urllib.request.Request(url, data=data, method=method, headers=headers)
  try:
    with urllib.request.urlopen(req, timeout=600) as r:
      body = r.read()
  except urllib.error.HTTPError as e:
    sys.exit(f"{method} {url}: {e.code} {e.read().decode(errors='replace')[:1000]}")
  return json.loads(body) if body else None


def latest_record():
  return call(
    "GET",
    f"{API}/records?q=conceptrecid:{CONCEPT_RECID}&allversions=true&sort=mostrecent&size=1",
  )["hits"]["hits"][0]


def main():
  pdf, version = Path(sys.argv[1]), sys.argv[2]
  metadata = json.loads((ROOT / ".zenodo.json").read_text())
  metadata["version"] = version
  metadata["publication_date"] = datetime.date.today().isoformat()

  latest = latest_record()
  if latest["metadata"].get("version") == version:
    sys.exit(f"версия {version} уже опубликована: {latest['links']['self_html']}")

  # newversion при существующем черновике возвращает этот же черновик.
  dep = call("POST", f"{API}/deposit/depositions/{latest['id']}/actions/newversion")
  draft = call("GET", dep["links"]["latest_draft"])

  for f in draft["files"]:
    call("DELETE", f["links"]["self"])
  call("PUT", draft["links"]["self"], json.dumps({"metadata": metadata}).encode())
  call("PUT", f"{draft['links']['bucket']}/{pdf.name}", pdf.read_bytes(), "application/octet-stream")
  done = call("POST", draft["links"]["publish"])
  print(f"{version}: {done['links']['html']} doi:{done['doi']}")


if __name__ == "__main__":
  main()
