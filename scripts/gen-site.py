#!/usr/bin/env python3
"""Сборка статического сайта payments.pq3.ru.

  python3 scripts/gen-site.py PDF VERSION OUTDIR

Метаданные берутся из .zenodo.json и CITATION.cff, оглавление из
src/parts/*/index.tex, превью обложки рендерит pdftoppm (poppler-utils),
карточку Open Graph собирает Pillow шрифтом PT Sans (fc-match).
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

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
URL = "https://payments.pq3.ru/"
# citation_pdf_url обязан указывать в тот же каталог, что и страница
# (требование Google Scholar), имя файла постоянно между релизами.
PDF_NAME = "payments-book.pdf"
SUBTITLE = "Карточные платежи, СБП и платёжная инфраструктура"
TEMPLATES = ("index.html", "sitemap.xml")


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
            m = re.search(
                r"\\chapter(?:\[[^]]*\])?\{([^}]*)\}",
                (ROOT / f"{name}.tex").read_text(encoding="utf-8"),
            )
            chapters.append(tex_to_text(m.group(1)))
        parts.append((tex_to_text(title), chapters))
    return parts


def font(pattern, size):
    path, index = subprocess.run(
        ["fc-match", "-f", "%{file}:%{index}", pattern],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rsplit(":", 1)
    return ImageFont.truetype(path, size, index=int(index))


def og_card(cover, dest, title, author):
    # 1200x630: широкая картинка, которую мессенджеры показывают крупным превью.
    w, h, pad = 1200, 630, 56
    img = Image.new("RGB", (w, h), "#0c2236")
    c = Image.open(cover).convert("RGB")
    ch = h - 2 * pad
    c = c.resize((round(c.width * ch / c.height), ch), Image.LANCZOS)
    img.paste(c, (pad + 8, pad))
    d = ImageDraw.Draw(img)
    x = pad + 8 + c.width + 64
    kicker, big, name, small = (
        font("PT Sans", 22),
        font("PT Sans:bold", 80),
        font("PT Sans:bold", 36),
        font("PT Sans", 28),
    )
    d.text((x, 118), "О Т К Р Ы Т А Я   К Н И Г А", font=kicker, fill="#9db4ca")
    y = 160
    for line in title.upper().split():
        d.text((x, y), line, font=big, fill="#dde8f3")
        y += 88
    d.text((x, y + 20), author, font=name, fill="#dde8f3")
    d.text((x, y + 76), SUBTITLE, font=small, fill="#9db4ca")
    d.text(
        (x, h - pad - 30),
        URL.removeprefix("https://").rstrip("/"),
        font=small,
        fill="#7fb2d9",
    )
    img.save(dest, optimize=True)


def main():
    pdf, version, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    date = datetime.date.fromisoformat(
        re.fullmatch(r"v(\d{4})\.(\d\d)\.(\d\d)", version).expand(r"\1-\2-\3")
    )
    meta = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    doi = re.search(
        r"value:\s*(10\.\S+)", (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    ).group(1)
    family, given = [p.strip() for p in meta["creators"][0]["name"].split(",")]
    orcid = meta["creators"][0]["orcid"]
    paras = [
        re.sub(r"<[^>]+>", "", p).strip()
        for p in re.findall(r"<p>(.*?)</p>", meta["description"])
    ]
    abstract_ru = (
        next(p for p in paras if p.startswith("RU.")).removeprefix("RU.").strip()
    )
    lead = abstract_ru.split(". ")[0].split(": ", 1)[1]
    og_description = lead[0].upper() + lead[1:] + "."
    abstract_en = (
        next(p for p in paras if p.startswith("EN.")).removeprefix("EN.").strip()
    )
    title = meta["title"].split(" (")[0]

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(pdf, out / PDF_NAME)
    for f in SITE.iterdir():
        if f.name not in TEMPLATES:
            shutil.copy(f, out / f.name)
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            "1",
            "-l",
            "1",
            "-singlefile",
            "-png",
            "-scale-to-x",
            "720",
            "-scale-to-y",
            "-1",
            str(pdf),
            str(out / "cover"),
        ],
        check=True,
    )
    og_card(out / "cover.png", out / "og.png", title, f"{given} {family}")

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
        "author": {
            "@type": "Person",
            "name": f"{given} {family}",
            "sameAs": f"https://orcid.org/{orcid}",
        },
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
        "encoding": {
            "@type": "MediaObject",
            "contentUrl": URL + PDF_NAME,
            "encodingFormat": "application/pdf",
        },
    }
    e = html.escape
    values = dict(
        title=e(title),
        author=e(f"{given} {family}"),
        citation_author=e(f"{family}, {given}"),
        citation_date=date.strftime("%Y/%m/%d"),
        year=date.year,
        version=e(version),
        date_ru=date.strftime("%d.%m.%Y"),
        lastmod=date.isoformat(),
        doi=e(doi),
        zenodo_recid=doi.rsplit(".", 1)[1],
        orcid=e(orcid),
        url=URL,
        pdf=PDF_NAME,
        pdf_mb=f"{pdf.stat().st_size / 1048576:.1f}".replace(".", ","),
        keywords=e("; ".join(meta["keywords"])),
        abstract_ru=e(abstract_ru),
        og_description=e(og_description),
        subtitle=e(SUBTITLE),
        abstract_en=e(abstract_en),
        toc=toc_html,
        jsonld=json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"),
    )
    for name in TEMPLATES:
        tpl = Template((SITE / name).read_text(encoding="utf-8"))
        (out / name).write_text(tpl.substitute(values), encoding="utf-8")
    print(f"{out}: {version}")


if __name__ == "__main__":
    main()
