#!/usr/bin/env python3
"""Сборка статического сайта payments.pq3.ru.

  python3 scripts/gen-site.py PDF VERSION OUTDIR

Название, подзаголовок, автор и оглавление с номерами страниц берутся
из самого PDF (pdfinfo, pdftohtml, pdftotext из poppler-utils), превью
обложки рендерит pdftoppm. Из репозитория того же тега: ORCID, ключевые
слова и аннотация из .zenodo.json, DOI из CITATION.cff, выдержка
из src/frontmatter/preface.tex, рисунок и его подпись. Карточку Open Graph
собирает Pillow шрифтом PT Sans (fc-match).
"""

import datetime
import html
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from string import Template

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
URL = "https://payments.pq3.ru/"
# citation_pdf_url обязан указывать в тот же каталог, что и страница
# (требование Google Scholar), имя файла постоянно между релизами.
PDF_NAME = "payments-book.pdf"
TEMPLATES = ("index.html", "sitemap.xml")
FIGURE = ("ch18-sbp", "sbp-c2b-flow")


def tex_to_text(s):
    s = s.replace("~", " ").replace("\\,", " ")
    s = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def tex_to_html(s):
    s = html.escape(re.sub(r"\s+", " ", s).strip(), quote=False)
    s = s.replace("---", "\u2014").replace("--", "\u2013").replace("~", "\u00a0")
    s = s.replace("\\,", "\u202f")
    for cmd, fmt in (
        ("enquote", "\u00ab{}\u00bb"),
        ("texttt", "<code>{}</code>"),
        ("textit", "<i>{}</i>"),
    ):
        s = re.sub(rf"\\{cmd}\{{([^}}]*)\}}", lambda m: fmt.format(m.group(1)), s)
    if "\\" in s:
        raise ValueError(f"TeX-команда без HTML-замены: {s}")
    return s


def preface():
    # Первые абзацы и абзац о первоисточниках; при правке предисловия
    # отсутствие абзаца-якоря останавливает сборку.
    text = re.sub(
        r"(?m)^\s*%.*$",
        "",
        (ROOT / "src" / "frontmatter" / "preface.tex").read_text(encoding="utf-8"),
    )
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip() and "\\addchap" not in p]
    rule = next(p for p in paras if p.lstrip().startswith("Я придерживался правила"))
    return [tex_to_html(p) for p in paras[:3] + [rule]]


def poppler(*args):
    return subprocess.run(
        args, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def pdf_meta(pdf):
    info = poppler("pdfinfo", "-enc", "UTF-8", str(pdf))
    return {
        k: re.search(rf"^{k}:\s*(.*)$", info, re.M).group(1).strip()
        for k in ("Title", "Subject", "Author")
    }


def pdf_pages(pdf):
    # Физическая страница файла -> печатный номер по назначениям hyperref page.N;
    # ссылка #page= указывает физическую страницу.
    out = poppler("pdfinfo", "-dests", str(pdf))
    printed = {}
    for m in re.finditer(r'^\s*(\d+) \[.*\] "page\.([^"]+)"$', out, re.M):
        printed.setdefault(int(m.group(1)), m.group(2))
    return printed


def toc(pdf):
    # Закладки PDF: верхний уровень - части (римский номер) и внетомные главы,
    # второй - главы с арабским номером. Возвращает [(часть, стр., [(N, глава, стр.)])].
    xml = poppler("pdftohtml", "-xml", "-i", "-stdout", "-f", "1", "-l", "1", str(pdf))
    root = ET.fromstring(xml[xml.index("<outline>") : xml.rindex("</outline>") + 10])
    parts, part = [], None
    for el in root:
        if el.tag == "item":
            m = re.fullmatch(r"([IVX]+) (.+)", el.text or "")
            part = (m.group(1), m.group(2), int(el.get("page")), []) if m else None
            if part:
                parts.append(part)
        elif el.tag == "outline" and part:
            for item in el.findall("item"):
                n, name = item.text.split(" ", 1)
                part[3].append((int(n), name, int(item.get("page"))))
    return parts


def figure_page(pdf, caption):
    # Страница рисунка по подписи "Рис. N - <подпись>" в тексте PDF.
    text = poppler("pdftotext", "-enc", "UTF-8", str(pdf), "-")
    want = re.escape(caption).replace(r"\ ", r"\s+")
    for phys, page in enumerate(text.split("\f"), 1):
        m = re.search(rf"Рис\.\s+(\d+)\s+\u2014\s+{want}", page)
        if m:
            return int(m.group(1)), phys
    raise ValueError(f"подпись рисунка не найдена в PDF: {caption}")


def font(pattern, size):
    path, index = subprocess.run(
        ["fc-match", "-f", "%{file}:%{index}", pattern],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rsplit(":", 1)
    return ImageFont.truetype(path, size, index=int(index))


def og_card(cover, dest, title, subtitle, author):
    # 1200x630: широкая картинка, которую мессенджеры показывают крупным превью.
    w, h, pad = 1200, 630, 56
    img = Image.new("RGB", (w, h), "#ffffff")
    c = Image.open(cover).convert("RGB")
    ch = h - 2 * pad
    c = c.resize((round(c.width * ch / c.height), ch), Image.LANCZOS)
    img.paste(c, (pad, pad))
    d = ImageDraw.Draw(img)
    d.rectangle((pad - 1, pad - 1, pad + c.width, pad + ch), outline="#d5d9e3")
    x = pad + c.width + 64
    big, name, small = (
        font("PT Sans:bold", 76),
        font("PT Sans", 36),
        font("PT Sans", 28),
    )
    y = 150
    for line in title.split():
        d.text((x, y), line, font=big, fill="#1a2030")
        y += 84
    d.text((x, y + 24), author, font=name, fill="#1a2030")
    line, y = "", y + 80
    for word in subtitle.split():
        if line and d.textlength(f"{line} {word}", font=small) > w - pad - x:
            d.text((x, y), line, font=small, fill="#5c647a")
            line, y = word, y + 38
        else:
            line = f"{line} {word}".strip()
    d.text((x, y), line, font=small, fill="#5c647a")
    d.text(
        (x, h - pad - 30),
        URL.removeprefix("https://").rstrip("/"),
        font=small,
        fill="#5c647a",
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
    info = pdf_meta(pdf)
    title, subtitle, author = info["Title"], info["Subject"], info["Author"]
    given, family = author.rsplit(" ", 1)
    orcid = meta["creators"][0]["orcid"]
    paras = [
        re.sub(r"<[^>]+>", "", p).strip()
        for p in re.findall(r"<p>(.*?)</p>", meta["description"])
    ]
    abstract_ru = (
        next(p for p in paras if p.startswith("RU.")).removeprefix("RU.").strip()
    )

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
    og_card(out / "cover.png", out / "og.png", title, subtitle, author)

    printed = pdf_pages(pdf)

    def entry(cls, num, name, phys):
        return (
            f'<a class="{cls}" href="{PDF_NAME}#page={phys}">'
            f'<span class="num">{num}</span><span class="name">{html.escape(name)}</span>'
            f'<span class="page">{printed[phys]}</span></a>'
        )

    fig_tex = next((ROOT / "src" / "parts").glob(f"part*/{FIGURE[0]}.tex"))
    caption = re.search(
        rf"\\includefigure\{{assets/figures/{FIGURE[0]}/{FIGURE[1]}\}}\s*\\caption\{{(.*?)\}}\\label",
        fig_tex.read_text(encoding="utf-8"),
        re.S,
    ).group(1)
    fig_num, fig_phys = figure_page(pdf, tex_to_text(caption))
    rows, fig_chapter = [], None
    for roman, part, phys, chapters in toc(pdf):
        rows.append(f"        <li>{entry('part', f'Часть {roman}', part, phys)}</li>")
        for n, name, ch_phys in chapters:
            rows.append(f"        <li>{entry('chapter', n, name, ch_phys)}</li>")
            if ch_phys <= fig_phys:
                fig_chapter = (n, name)
    toc_html = "\n".join(rows)
    shutil.copy(
        ROOT / "assets" / "figures" / FIGURE[0] / f"{FIGURE[1]}.svg",
        out / "figure.svg",
    )
    ld = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": title,
        "alternateName": "Payments Engineering",
        "author": {
            "@type": "Person",
            "name": author,
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
        author=e(author),
        citation_author=e(f"{family}, {given}"),
        citation_date=date.strftime("%Y/%m/%d"),
        year=date.year,
        version=e(version),
        date_ru=date.strftime("%d.%m.%Y"),
        lastmod=date.isoformat(),
        doi=e(doi),
        orcid=e(orcid),
        url=URL,
        pdf=PDF_NAME,
        pdf_mb=f"{pdf.stat().st_size / 1048576:.1f}".replace(".", ","),
        keywords=e("; ".join(meta["keywords"])),
        abstract_ru=e(abstract_ru),
        subtitle=e(subtitle),
        preface="\n".join(f"        <p>{p}</p>" for p in preface()),
        preface_page=next(k for k, v in printed.items() if v == "1"),
        figure_caption=tex_to_html(caption),
        figure_alt=e(tex_to_text(caption)),
        figure_num=fig_num,
        figure_chapter=f"гл.\u00a0{fig_chapter[0]} \u00ab{e(fig_chapter[1])}\u00bb",
        figure_href=f"{PDF_NAME}#page={fig_phys}",
        figure_page=printed[fig_phys],
        toc=toc_html,
        jsonld=json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"),
    )
    for name in TEMPLATES:
        tpl = Template((SITE / name).read_text(encoding="utf-8"))
        (out / name).write_text(tpl.substitute(values), encoding="utf-8")
    print(f"{out}: {version}")


if __name__ == "__main__":
    main()
