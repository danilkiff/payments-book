#!/usr/bin/env python3
"""Генерирует self-contained fix-workflow из build/reflow-fixplan-r1.json.
Один агент на файл (файлы различны → нет конфликтов записи). Агенты НЕ собирают.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "build" / "reflow-fixplan-r1.json").read_text(encoding="utf-8"))

HEADER = (
    "export const meta = {\n"
    "  name: 'reflow-fix-r1',\n"
    "  description: 'Применение round-1 правок типографской вычитки (один агент на файл)',\n"
    "  phases: [\n"
    "    { title: 'FixSVG', detail: 'правка hand-drawn SVG и генераторов по канону' },\n"
    "    { title: 'FixText', detail: 'правка .tex/.bib/.py: типографика и размещение' },\n"
    "  ],\n"
    "}\n\n"
)
DATA = "const PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n\n"

BODY = r"""
const CANON = 'assets/figures/README.md';
const PALETTE = '#1A2030 #5C647A #E8ECF7 #F5F7FD #4E63D9 #7759D6 #2F8B67 #B8821C #C15462 #ffffff';

const GUARD = [
  'ОБЩИЕ ПРАВИЛА (строго):',
  '• Применяй ТОЛЬКО перечисленные ниже находки этого файла. Если предложенный фикс очевидно',
  '  неверен — примени корректный минимальный вариант и отметь это в notes.',
  '• НИКОГДА не переделывай информационную структуру фигуры: не превращай flow в decision-tree,',
  '  топологию в Венн, не перекомпоновывай слои, не переименовывай ветви решений новой доменной',
  '  семантикой, не объединяй/не разделяй понятия. Если находка требует РЕДИЗАЙНА жанра —',
  '  пропусти её (skipped) и опиши. Применяй только канон-часть, если она отделима',
  '  (пример: у pci-cde-boundary настоящий фикс — удалить дублирующий ellipse3, а НЕ рисовать Венн).',
  '• НЕ переименовывай файлы. НЕ меняй смысл прозы — в .tex применяй только описанную',
  '  типографско-верстальную правку (тире, неразрывный пробел, \\mbox, %, размещение флоата,',
  '  \\needspace, мягкий перенос, снятие \\pagebreak), сохраняя формулировки.',
  '• КАТЕГОРИЧЕСКИ НЕ запускай сборку: ни make, ни latexmk, ни make svg, ни scripts/build.sh.',
  '  Сборку делает оркестратор отдельно и серийно.',
].join('\n');

const SVG_RULES = [
  `КАНОН ФИГУР — прочитай ${CANON}. Палитра (только эти + #ffffff): ${PALETTE}.`,
  'Это hand-drawn SVG — правится напрямую. После правки ОБЯЗАТЕЛЬНО проверь (Bash):',
  '  1) xmllint --noout <svg>  — XML валиден;',
  '  2) grep -oE "#[0-9a-fA-F]{6}" <svg> | sort -u  — подмножество палитры; любой канон-цвет в',
  '     нижнем регистре ПРИВЕДИ К ВЕРХНЕМУ (#5c647a → #5C647A): канон — uppercase, #ffffff — исключение;',
  '  3) grep -oE \'id="arr-[^"]*"\' <svg> | sort -u  — только шесть arr-AccentA/AccentB/Good/Warn/Bad/Muted',
  '     (+ "-s"); Inkscape-дубли (arr-muted-1, arr-muted-s-8-7…) удали из defs и перенаправь marker-* на',
  '     канонический; цвет marker обязан совпадать с цветом линии (иначе стрелка «оторвана»);',
  '  4) fill-opacity: 0.15 для всех цветов, КРОМЕ Warn #B8821C = 0.18; Panel/Soft — сплошные без opacity;',
  '  5) рендер-проверка: rsvg-convert <svg> -o /tmp/<basename>.png  (НЕ make svg!);',
  '  6) шрифт ≥ 9pt; Unicode-операторы (→ ↔ ⊕) в <text> заменить словами/ASCII (Inkscape ломает PDF).',
].join('\n');

const GEN_RULES = [
  `Это СГЕНЕРИРОВАННАЯ фигура: правь ТОЛЬКО Python-генератор, НЕ .svg (он перезатрётся).`,
  `Канон палитры/шрифта — в scripts/figures/_common.py и ${CANON}.`,
  'После правки: 1) запусти `python3 <этот gen-скрипт>` чтобы перегенерировать .svg;',
  '2) xmllint --noout <выходной svg>; 3) grep палитры (uppercase canon); 4) rsvg-convert в /tmp.',
  'НЕ запускай make svg / make pdf.',
].join('\n');

function findingsBlock(items) {
  return items.map((it, i) =>
    `  ${i + 1}) [${it.severity}/${it.category}]${it.page ? ' p' + it.page : ''}\n` +
    `     ПРОБЛЕМА: ${it.problem}\n` +
    `     ПРЕДЛОЖЕННЫЙ ФИКС: ${it.fix}`
  ).join('\n');
}

function prompt(p) {
  const head = [
    `Ты применяешь финальные типографские правки к ОДНОМУ файлу книги «Инженерия платежей».`,
    `ФАЙЛ: ${p.file}  (kind=${p.kind})`,
    '',
    GUARD,
    '',
  ];
  let rules = '';
  if (p.kind === 'svg') rules = SVG_RULES + '\n';
  else if (p.kind === 'generator') rules = GEN_RULES + '\n';
  else if (p.kind === 'tex') rules = 'Это .tex. Применяй только верстально-типографскую правку. НЕ собирай.\n';
  else if (p.kind === 'py') rules = 'Это Python-сэмпл, попадающий в печатный листинг. Поправь только указанный комментарий/текст, не логику.\n';
  else if (p.kind === 'bib') rules = 'Это .bib. Поправь только указанный разделитель/строку в title, сохранив ключи и поля.\n';
  const tail = [
    '',
    'НАХОДКИ ПО ЭТОМУ ФАЙЛУ:',
    findingsBlock(p.items),
    '',
    'Прочитай файл, локализуй каждую находку, примени правку, проверь по правилам выше.',
    'Верни строго: {file, status: done|partial|skipped|error, applied:[{finding, change}],',
    'skipped:[{finding, reason}], verify, notes}. verify — краткий итог проверок (для svg/generator:',
    'xmllint/палитра/маркеры/rsvg; иначе "n/a"). Будь честен: что не применил — в skipped с причиной.',
  ];
  return head.join('\n') + rules + tail.join('\n');
}

const FIX_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    file: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'skipped', 'error'] },
    applied: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { finding: { type: 'string' }, change: { type: 'string' } },
      required: ['finding', 'change'] } },
    skipped: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { finding: { type: 'string' }, reason: { type: 'string' } },
      required: ['finding', 'reason'] } },
    verify: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['file', 'status', 'applied', 'skipped', 'verify', 'notes'],
};

const svgJobs = PLAN.filter(p => p.kind === 'svg' || p.kind === 'generator');
const textJobs = PLAN.filter(p => p.kind === 'tex' || p.kind === 'py' || p.kind === 'bib');
log(`Fix round-1: ${svgJobs.length} фигур (svg/gen) + ${textJobs.length} текст/прочее = ${PLAN.length} файлов`);

phase('FixSVG');
const svgRes = await parallel(svgJobs.map(p => () =>
  agent(prompt(p), { label: `fix:${p.file.split('/').pop()}`, phase: 'FixSVG', schema: FIX_SCHEMA })
));

phase('FixText');
const textRes = await parallel(textJobs.map(p => () =>
  agent(prompt(p), { label: `fix:${p.file.split('/').pop()}`, phase: 'FixText', schema: FIX_SCHEMA })
));

const all = [...svgRes, ...textRes].filter(Boolean);
const byStatus = {};
for (const r of all) byStatus[r.status] = (byStatus[r.status] || 0) + 1;
log(`Fix готов: ${all.length}/${PLAN.length} файлов, статусы ${JSON.stringify(byStatus)}`);
return { results: all };
"""

out = ROOT / "build" / "reflow-fix.workflow.js"
out.write_text(HEADER + DATA + BODY, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes); files={len(plan)}")
