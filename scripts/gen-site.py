#!/usr/bin/env python3
"""Сборка статического сайта payments.pq3.ru.

  python3 scripts/gen-site.py PDF VERSION OUTDIR

Метаданные берутся из .zenodo.json и CITATION.cff, оглавление из
src/parts/*/index.tex, превью обложки рендерит pdftoppm (poppler-utils).
"""
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
URL = "https://payments.pq3.ru/"
# citation_pdf_url обязан указывать в тот же каталог, что и страница
# (требование Google Scholar), имя файла постоянно между релизами.
PDF_NAME = "payments-book.pdf"


def tex_to_text(s):
  s = s.replace("~", " ").replace("\\,", " ")
  s = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", s)
  return re.sub(r"\s+", " ", s).strip()


def toc():
  parts = []
  for index in sorted((ROOT / "src" / "parts").glob("part*/index.tex")):
    text = re.sub(r"(?m)^\s*%.*$", "", index.read_text(encoding="utf-8"))
    title = re.search(r"\\part\{([^}]*)\}", text).group(1)
    chapters = []
    for name in re.findall(r"\\input\{(src/parts/part\d+/ch[^}]*)\}", text):
      m = re.search(r"\\chapter(?:\[[^]]*\])?\{([^}]*)\}", (ROOT / f"{name}.tex").read_text(encoding="utf-8"))
      chapters.append(tex_to_text(m.group(1)))
    parts.append((tex_to_text(title), chapters))
  return parts


def main():
  pdf, version, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
  date = datetime.date.fromisoformat(re.fullmatch(r"v(\d{4})\.(\d\d)\.(\d\d)", version).expand(r"\1-\2-\3"))
  meta = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
  doi = re.search(r"value:\s*(10\.\S+)", (ROOT / "CITATION.cff").read_text(encoding="utf-8")).group(1)
  family, given = [p.strip() for p in meta["creators"][0]["name"].split(",")]
  orcid = meta["creators"][0]["orcid"]
  paras = [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<p>(.*?)</p>", meta["description"])]
  abstract_ru = next(p for p in paras if p.startswith("RU.")).removeprefix("RU.").strip()
  abstract_en = next(p for p in paras if p.startswith("EN.")).removeprefix("EN.").strip()
  title = meta["title"].split(" (")[0]

  if out.exists():
    shutil.rmtree(out)
  out.mkdir(parents=True)
  shutil.copy(pdf, out / PDF_NAME)
  for f in SITE.iterdir():
    if f.name != "index.html":
      shutil.copy(f, out / f.name)
  subprocess.run(
    ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-png", "-scale-to-x", "720", "-scale-to-y", "-1", str(pdf), str(out / "cover")],
    check=True,
  )

  toc_html = "\n".join(
    f'        <li><span class="part">{html.escape(p)}</span>\n          <ol>\n'
    + "\n".join(f"            <li>{html.escape(c)}</li>" for c in chs)
    + "\n          </ol>\n        </li>"
    for p, chs in toc()
  )
  ld = {
    "@context": "https://schema.org",
    "@type": "Book",
    "name": title,
    "alternateName": "Payments Engineering",
    "author": {"@type": "Person", "name": f"{given} {family}", "sameAs": f"https://orcid.org/{orcid}"},
    "inLanguage": "ru",
    "datePublished": date.isoformat(),
    "version": version,
    "bookFormat": "https://schema.org/EBook",
    "isAccessibleForFree": True,
    "license": "https://creativecommons.org/licenses/by-nc/4.0/",
    "identifier": f"https://doi.org/{doi}",
    "url": URL,
    "image": URL + "cover.png",
    "keywords": ", ".join(meta["keywords"]),
    "description": abstract_ru,
    "encoding": {"@type": "MediaObject", "contentUrl": URL + PDF_NAME, "encodingFormat": "application/pdf"},
  }
  e = html.escape
  page = Template((SITE / "index.html").read_text(encoding="utf-8")).substitute(
    title=e(title),
    author=e(f"{given} {family}"),
    citation_author=e(f"{family}, {given}"),
    citation_date=date.strftime("%Y/%m/%d"),
    year=date.year,
    version=e(version),
    date_ru=date.strftime("%d.%m.%Y"),
    doi=e(doi),
    zenodo_recid=doi.rsplit(".", 1)[1],
    orcid=e(orcid),
    url=URL,
    pdf=PDF_NAME,
    pdf_mb=f"{pdf.stat().st_size / 1048576:.1f}".replace(".", ","),
    keywords=e("; ".join(meta["keywords"])),
    abstract_ru=e(abstract_ru),
    abstract_en=e(abstract_en),
    toc=toc_html,
    jsonld=json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"),
  )
  (out / "index.html").write_text(page, encoding="utf-8")
  print(f"{out}: {version}, {len(page)} bytes")


if __name__ == "__main__":
  main()
