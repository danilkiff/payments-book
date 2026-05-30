#!/usr/bin/env python3
"""Генерирует self-contained workflow-скрипт для аудита вёрстки.

Читает build/reflow-manifest.json + build/svg-canon-scan.json, встраивает
компактный скелет (страницы/пути + срез детерминированного скана) прямо в JS
(у workflow-скриптов нет доступа к ФС), пишет build/reflow-audit.workflow.js.
Сами PNG/SVG/спеку/канон агенты читают своими тулзами.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))
scan = json.loads((ROOT / "build" / "svg-canon-scan.json").read_text(encoding="utf-8"))
svg_scan = scan["svgs"]
includes = scan["includes"]

units = []
fig_units = []
for u in manifest:
    tex = u["tex"]
    fig_files = [{"file": s["file"], "generated": s["generated"]} for s in u["svgs"]]
    units.append({
        "key": u["key"], "num": u["num"], "tex": tex, "figDir": u["fig_dir"],
        "first": u["first_page"], "last": u["last_page"],
        "figs": fig_files,
    })
    if u["fig_dir"]:
        dirname = Path(u["fig_dir"]).name
        svgs = []
        for s in u["svgs"]:
            rel = f"{dirname}/{Path(s['file']).name}"
            sc = svg_scan.get(rel, {})
            svgs.append({
                "file": s["file"], "generated": s["generated"],
                "scan": {
                    "off_palette": sc.get("off_palette", []),
                    "off_markers": sc.get("off_markers", []),
                    "off_opacity": sc.get("off_opacity", []),
                    "all_opacity": sc.get("all_opacity", []),
                    "used_markers": sc.get("used_markers", []),
                    "small_fonts_lt9": sc.get("small_fonts_lt9", []),
                    "viewBox": sc.get("viewBox"), "aspect": sc.get("aspect"),
                },
            })
        fig_units.append({
            "key": u["key"], "figDir": u["fig_dir"],
            "first": u["first_page"], "last": u["last_page"],
            "svgs": svgs,
            "includes": includes.get(tex, []) if isinstance(tex, str) else [],
        })

payload = {"pngDir": "build/page-pngs/all", "units": units, "figUnits": fig_units}

HEADER = (
    "export const meta = {\n"
    "  name: 'reflow-audit',\n"
    "  description: 'Финальная типографская вычитка: ревью страниц (vision) + аудит фигур по канону',\n"
    "  phases: [\n"
    "    { title: 'Review',      detail: 'vision-ревью отрендеренных страниц по чанкам' },\n"
    "    { title: 'Figures',     detail: 'аудит SVG-фигур против канона по каталогам' },\n"
    "    { title: 'Consistency', detail: 'сквозная согласованность фигур (lifeline/масштаб/маркеры)' },\n"
    "  ],\n"
    "}\n\n"
)

DATA = "const DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n\n"

# ---- JS body: без python-интерполяции, шаблонные литералы безопасны ----
BODY = r"""
const PNG = DATA.pngDir;
const pad = n => String(n).padStart(3, '0');
const pagePaths = (a, b) => { const r = []; for (let p = a; p <= b; p++) r.push(`${PNG}/p${pad(p)}.png`); return r; };

// ---------- схемы структурированного вывода ----------
const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    unit: { type: 'string' },
    part: { type: 'string' },
    pagesSeen: { type: 'array', items: { type: 'integer' } },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          page: { type: 'integer' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          category: { type: 'string', enum: [
            'whitespace', 'pagebreak', 'widow-orphan', 'overfull', 'underfull',
            'hyphenation', 'dash', 'quotes', 'nbsp-preposition', 'heading-position',
            'table', 'figure-scale', 'figure-color', 'figure-arrow', 'figure-overlap',
            'figure-readability', 'caption-length', 'footnote-folio', 'list', 'other'] },
          where: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
          target: { type: 'string' },
        },
        required: ['page', 'severity', 'category', 'where', 'problem', 'fix', 'target'],
      },
    },
  },
  required: ['unit', 'part', 'pagesSeen', 'findings'],
};

const FIGDIR_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    dir: { type: 'string' },
    figures: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          svg: { type: 'string' },
          generated: { type: 'boolean' },
          genre: { type: 'string' },
          onPage: { type: 'integer' },
          lifeline: {
            type: 'object', additionalProperties: false,
            properties: {
              present: { type: 'boolean' },
              color: { type: 'string' }, dash: { type: 'string' }, width: { type: 'string' },
            },
            required: ['present', 'color', 'dash', 'width'],
          },
          issues: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false,
              properties: {
                severity: { type: 'string', enum: ['high', 'medium', 'low'] },
                category: { type: 'string' },
                problem: { type: 'string' },
                fix: { type: 'string' },
                fixTarget: { type: 'string', enum: ['svg', 'generator', 'tex'] },
              },
              required: ['severity', 'category', 'problem', 'fix', 'fixTarget'],
            },
          },
        },
        required: ['svg', 'generated', 'genre', 'onPage', 'lifeline', 'issues'],
      },
    },
  },
  required: ['dir', 'figures'],
};

const CONS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          theme: { type: 'string' },
          problem: { type: 'string' },
          affected: { type: 'array', items: { type: 'string' } },
          fix: { type: 'string' },
        },
        required: ['severity', 'theme', 'problem', 'affected', 'fix'],
      },
    },
  },
  required: ['findings'],
};

const SPEC = 'docs/reflow/_review-spec.md';
const CANON = 'assets/figures/README.md';

// ---------- фаза 1: ревью страниц ----------
const CHUNK = 13;
const reviewChunks = [];
for (const u of DATA.units) {
  const n = u.last - u.first + 1;
  const cc = Math.max(1, Math.ceil(n / CHUNK));
  const sz = Math.ceil(n / cc);
  for (let i = 0; i < cc; i++) {
    const f = u.first + i * sz;
    if (f > u.last) break;
    const l = Math.min(u.last, f + sz - 1);
    reviewChunks.push({ u, f, l, part: `${i + 1}/${cc}` });
  }
}
log(`Review: ${reviewChunks.length} чанков по ≤${CHUNK} страниц над ${DATA.units.length} разделами`);

function reviewPrompt(c) {
  const u = c.u;
  const texList = Array.isArray(u.tex) ? u.tex.join(', ') : (u.tex || '—');
  const figList = u.figs.length
    ? u.figs.map(f => `${f.file}${f.generated ? ' [GENERATED→править генератор]' : ''}`).join('; ')
    : '—';
  const imgs = pagePaths(c.f, c.l);
  return [
    'Ты — типографский корректор финальной вычитки книги «Инженерия платежей» (русский, печать).',
    `Раздел: ${u.key} (часть ${c.part}). Печатные страницы ${c.f}–${c.l}.`,
    `Источник прозы: ${texList}.  Каталог фигур: ${u.figDir || '—'}.`,
    `Фигуры главы: ${figList}.`,
    '',
    'СНАЧАЛА прочитай две спеки (это твои критерии):',
    `  • ${SPEC} — что фиксировать и severity;`,
    `  • ${CANON} — палитра/маркеры/толщины/шрифт фигур.`,
    'Затем внимательно ПОСМОТРИ каждую страницу-картинку ниже (это рендер 150 DPI, что видит читатель):',
    ...imgs.map(p => `  ${p}`),
    '',
    'Фиксируй ТОЛЬКО реально видимые дефекты. Приоритет (по запросу автора на печать):',
    '  1) пустоты и разрывы: большие дыры внизу/в середине полосы, полупустая страница из-за',
    '     всплывшей фигуры, заголовок у нижнего поля без текста, неудачный разрыв;',
    '  2) масштаб фигур: фигура раздута на всю полосу или наоборот мелкая; соседние однотипные',
    '     фигуры разного масштаба; большие боковые поля у height-capped фигуры;',
    '  3) цвет/единообразие фигур: цвет вне канона, бледная/пёстрая заливка, разнобой;',
    '     ОСОБОЕ внимание — lifeline в sequence-диаграммах (вертикали должны быть одинаковы:',
    '     цвет Muted, пунктир, тонкая линия), и единообразие оформления;',
    '  4) стрелки: выходят/входят не из того угла блока, «оторваны» от линии (цвет маркера ≠',
    '     цвет линии), наложение текста на текст/на линию, обрезанный текст в фигуре;',
    '  5) типографика: висячие строки и предлоги, переполнение за поле (overfull), дефис вместо',
    '     тире, прямые кавычки, длинная подпись \\caption (>2 строк), кривые таблицы.',
    '',
    'НЕ считай дефектом штатную книжную вёрстку: открытие главы с новой полосы и отбивка сверху,',
    'короткая последняя полоса главы, нормальные интервалы между разделами, висячая строка',
    'НЕ на стыке страниц. Дефект пустоты — это дыра ВНУТРИ полосы (всплывшая фигура оставила',
    'полполосы пустой, заголовок улетел вниз, таблица/фигура вытолкнула текст).',
    '',
    'Для КАЖДОЙ находки укажи: page (печатный номер), severity, category, where (место на полосе),',
    'problem (что не так), fix (правка на уровне ИСХОДНИКА — .tex/.svg/генератор), target (файл,',
    'если ясен: для фигур — путь .svg ИЛИ scripts/figures/gen_*.py если [GENERATED], для прозы — .tex).',
    'Generated-фигуры правятся ТОЛЬКО через генератор, не .svg. Чистые страницы не упоминай.',
    'Не выдумывай дефекты; если страница чистая — не добавляй находок по ней.',
    `Верни {unit:"${u.key}", part:"${c.part}", pagesSeen:[...], findings:[...]}.`,
  ].join('\n');
}

phase('Review');
const reviewResults = await parallel(
  reviewChunks.map(c => () =>
    agent(reviewPrompt(c), {
      label: `review:${c.u.key}#${c.part}`,
      phase: 'Review',
      schema: REVIEW_SCHEMA,
    })
  )
);
const review = reviewResults.filter(Boolean);
const nFind = review.reduce((a, r) => a + (r.findings ? r.findings.length : 0), 0);
log(`Review готов: ${review.length}/${reviewChunks.length} чанков, ${nFind} находок`);

// ---------- фаза 2: аудит фигур по каталогам ----------
function figPrompt(fu) {
  const svgList = fu.svgs.map(s => {
    const sc = s.scan;
    const flags = [];
    if (sc.off_palette && sc.off_palette.length) flags.push(`off-hex=${JSON.stringify(sc.off_palette)}`);
    if (sc.off_markers && sc.off_markers.length) flags.push(`off-markers=${JSON.stringify(sc.off_markers)}`);
    if (sc.off_opacity && sc.off_opacity.length) flags.push(`off-opacity=${JSON.stringify(sc.off_opacity)}`);
    if (sc.small_fonts_lt9 && sc.small_fonts_lt9.length) flags.push(`font<9=${JSON.stringify(sc.small_fonts_lt9)}`);
    const vb = sc.viewBox ? `vb=${sc.viewBox[0]}x${sc.viewBox[1]} aspect=${sc.aspect}` : '';
    return `  ${s.file}${s.generated ? ' [GENERATED]' : ''}  ${vb}  ${flags.length ? 'СКАН: ' + flags.join(' ') : ''}`;
  }).join('\n');
  const inc = (fu.includes || []).map(i =>
    `  ${i.target}  width=${i.width_frac != null ? i.width_frac + '·\\linewidth' : (i.width_abs || 'default(\\linewidth)')}`
  ).join('\n') || '  (нет явных width — все на \\linewidth, клампятся по height=.45\\textheight)';
  return [
    'Ты — ревьюер инженерных иллюстраций книги «Инженерия платежей». Аудит фигур одного каталога.',
    `Каталог: ${fu.figDir}. Глава на печатных страницах ${fu.first}–${fu.last}.`,
    `Канон обязателен к прочтению: ${CANON}. Детерминированный предскан строк уже дан ниже —`,
    'подтверди/опровергни его глазами по исходнику и по рендеру.',
    '',
    'SVG в каталоге (читай КАЖДЫЙ файл целиком):',
    svgList,
    '',
    'Как фигуры включены в .tex (масштаб на полосе):',
    inc,
    '',
    `Рендер страниц главы (чтобы увидеть фигуру на полосе): ${PNG}/p${pad(fu.first)}.png … p${pad(fu.last)}.png`,
    '',
    'Для каждой фигуры определи: genre (sequence/state/topology/decision/matrix/anatomy/timeline/other),',
    'onPage (печатная страница, где она стоит), lifeline (если sequence: есть ли вертикальные линии-',
    'жизни, их цвет/пунктир/толщина — для проверки единообразия по книге).',
    'Заведи issues по канону:',
    '  • цвет вне палитры (10 hex + #fff); пёстрая/Excalidraw-пастель;',
    '  • fill-opacity ≠ 0.15 (0.18 для Warn) — слишком бледно/ярко (off-opacity из скана);',
    '  • неканоничные id маркеров (не из шести arr-*; Inkscape-дубли arr-muted-1 и т.п.);',
    '  • цвет маркера ≠ цвет линии (стрелка «оторвана»); стрелка из неправильного угла;',
    '  • шрифт <9pt (нечитаемо на печати); текст-на-тексте, вылет за блок;',
    '  • «школьная блок-схема» (по канону — переделать жанр или удалить);',
    '  • масштаб: фигура раздута/мелка относительно соседних того же жанра.',
    'fixTarget: "generator" если [GENERATED] (правка идёт в scripts/figures/gen_*.py, НЕ в .svg),',
    'иначе "svg"; "tex" если правка только в ширине включения.',
    `Верни {dir:"${fu.figDir}", figures:[...]}. Если фигура канонична — пустой issues, но genre/lifeline заполни.`,
  ].join('\n');
}

phase('Figures');
const figResults = await parallel(
  DATA.figUnits.map(fu => () =>
    agent(figPrompt(fu), {
      label: `fig:${fu.figDir.split('/').pop()}`,
      phase: 'Figures',
      schema: FIGDIR_SCHEMA,
    })
  )
);
const figures = figResults.filter(Boolean);
const nIssues = figures.reduce((a, d) => a + d.figures.reduce((b, f) => b + (f.issues ? f.issues.length : 0), 0), 0);
log(`Figures готов: ${figures.length}/${DATA.figUnits.length} каталогов, ${nIssues} issue`);

// ---------- фаза 3: сквозная согласованность ----------
phase('Consistency');
const allFigs = figures.flatMap(d => d.figures.map(f => ({
  svg: f.svg, genre: f.genre, generated: f.generated,
  lifeline: f.lifeline, onPage: f.onPage,
})));
const consPrompt = [
  'Ты — арт-директор книги. Перед тобой сводка ВСЕХ фигур книги (жанр, lifeline, страница).',
  'Найди СКВОЗНЫЕ нарушения единообразия между фигурами (то, что не видно на одной фигуре):',
  '  • lifeline: в sequence-диаграммах вертикали-жизни оформлены по-разному (цвет/пунктир/толщина);',
  '  • масштаб: однотипные фигуры (один genre) включены сильно разной ширины → на печати разный кегль;',
  '  • маркеры: где-то каноничные arr-*, где-то Inkscape-дубли;',
  '  • палитра/заливки: разнобой fill-opacity между однотипными фигурами.',
  `Канон: ${CANON}. Сводка фигур (JSON):`,
  JSON.stringify(allFigs),
  '',
  'Верни {findings:[{severity, theme, problem, affected:[svg-пути], fix}]}. Только реальные расхождения.',
].join('\n');
const consistency = await agent(consPrompt, { label: 'consistency', phase: 'Consistency', schema: CONS_SCHEMA });

return { review, figures, consistency };
"""

out = ROOT / "build" / "reflow-audit.workflow.js"
out.write_text(HEADER + DATA + BODY, encoding="utf-8")
size = out.stat().st_size
print(f"wrote {out.relative_to(ROOT)}  ({size} bytes)")
print(f"units={len(units)}  figUnits={len(fig_units)}")
