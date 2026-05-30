#!/usr/bin/env python3
"""Генерирует vision-workflow для round-2 полировки пагинации.

Вход: build/polish-candidates.json (детектор) + build/reflow-manifest.json.
Группирует кандидаты по главам; на главу — один агент: смотрит страницы-кандидаты
(+ соседние) и читает .tex главы, отделяет реальные дефекты (mid-content пустота,
одиночная строка-вдова, заголовок-сирота, всплывший [H]-флоат) от штатных (конец
главы, зазор внутри фигуры, списки back-matter) и предлагает минимальную правку
исходника. Пишет build/polish-audit.workflow.js.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cands = json.loads((ROOT / "build" / "polish-candidates.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))

tex_for_key = {u["key"]: u["tex"] for u in manifest}
range_for_key = {u["key"]: (u["first_page"], u["last_page"]) for u in manifest}

by_ch = defaultdict(list)
for c in cands:
    by_ch[c["chapter"]].append(c)

groups = []
for ch, items in by_ch.items():
    tex = tex_for_key.get(ch)
    groups.append({
        "chapter": ch,
        "tex": tex if isinstance(tex, str) else (tex[0] if isinstance(tex, list) and tex else None),
        "texAll": tex if isinstance(tex, list) else ([tex] if tex else []),
        "range": range_for_key.get(ch),
        "items": [{"page": c["page"], "kind": c["kind"],
                   "bottom": c["bottom"], "gap": c["gap"], "span": c["span"]} for c in items],
    })

payload = {"pngDir": "build/page-pngs/all", "groups": groups}

HEADER = (
    "export const meta = {\n"
    "  name: 'polish-audit',\n"
    "  description: 'Round-2 полировка пагинации: классификация пустот/вдов/сирот-заголовков по главам',\n"
    "  phases: [ { title: 'Classify', detail: 'агент на главу: страницы-кандидаты + .tex → реальные дефекты и правки' } ],\n"
    "}\n\n"
)
DATA = "const DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n\n"

BODY = r"""
const PNG = DATA.pngDir;
const pad = n => String(n).padStart(3, '0');

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    chapter: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          page: { type: 'integer' },
          isDefect: { type: 'boolean' },
          type: { type: 'string', enum: [
            'bottom-void', 'widow-lone-line', 'heading-orphan', 'table-float-void',
            'figure-internal', 'chapter-end-normal', 'backmatter-normal', 'other-normal'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          cause: { type: 'string' },
          fixFile: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['page', 'isDefect', 'type', 'severity', 'cause', 'fixFile', 'fix'],
      },
    },
  },
  required: ['chapter', 'findings'],
};

function prompt(g) {
  const lines = [];
  lines.push('Ты — типографский корректор round-2 (полировка пагинации) книги «Инженерия платежей» (печать, B5).');
  lines.push(`Глава: ${g.chapter}. Исходник: ${(g.texAll || []).join(', ') || '—'}.`);
  if (g.range) lines.push(`Печатные страницы главы: ${g.range[0]}–${g.range[1]}.`);
  lines.push('');
  lines.push('Детектор пометил эти полосы как подозрительные на пустоту (bottom=нижний недобор, gap=внутренний разрыв, span=доля полосы с текстом, меньше=пустее):');
  for (const it of g.items) {
    lines.push(`  • p${it.page} [${it.kind}] bottom=${it.bottom} gap=${it.gap} span=${it.span}  → ${PNG}/p${pad(it.page)}.png (сосед: ${PNG}/p${pad(it.page + 1)}.png)`);
  }
  lines.push('');
  lines.push('ДЛЯ КАЖДОЙ полосы: ПОСМОТРИ её PNG и PNG соседней страницы, при необходимости прочитай .tex главы.');
  lines.push('Реши, РЕАЛЬНЫЙ ли это дефект печати или штатная вёрстка:');
  lines.push('  • bottom-void — текст обрывается высоко, низ полосы пустой из-за всплывшего флота/таблицы/заголовка (ДЕФЕКТ);');
  lines.push('  • widow-lone-line — на полосе одиноко висит короткий абзац/строка-хвост, остальное пусто или это начало (ДЕФЕКТ);');
  lines.push('  • heading-orphan — заголовок раздела у самого нижнего поля без текста под ним (ДЕФЕКТ);');
  lines.push('  • table-float-void — [H]-таблица/figure не поместилась и оставила дыру (ДЕФЕКТ);');
  lines.push('  • figure-internal — «пустота» это законные поля ВНУТРИ фигуры (НЕ дефект);');
  lines.push('  • chapter-end-normal — последняя полоса главы, естественно короткая (НЕ дефект);');
  lines.push('  • backmatter-normal — список первоисточников/глоссарий/колофон, естественные разрывы (НЕ дефект);');
  lines.push('  • other-normal — иное штатное (НЕ дефект).');
  lines.push('');
  lines.push('Если ДЕФЕКТ: найди причину в .tex (всплывший [H]/[tbp]-флоат, \\FloatBarrier перед \\section, лишний \\needspace,');
  lines.push('одиночный короткий абзац, крупный объект) и предложи МИНИМАЛЬНУЮ правку: [H]→[tbp]/[t], снять/ослабить \\FloatBarrier,');
  lines.push('\\needspace↓, слить одиночный абзац с соседним, перенести блок \\begin{figure} после абзаца (как пустоту заполнить флотом).');
  lines.push('Прозу автора НЕ переписывать без нужды; склейка абзацев и перенос флота — допустимы.');
  lines.push('fixFile — путь .tex; fix — что именно изменить (с якорным текстом/строкой). Для НЕ-дефекта fix="—".');
  lines.push(`Верни {chapter:"${g.chapter}", findings:[{page,isDefect,type,severity,cause,fixFile,fix}]}.`);
  return lines.join('\n');
}

phase('Classify');
log(`Polish: ${DATA.groups.length} глав, ${DATA.groups.reduce((a,g)=>a+g.items.length,0)} полос-кандидатов`);
const results = await parallel(
  DATA.groups.map(g => () => agent(prompt(g), { label: `polish:${g.chapter}`, phase: 'Classify', schema: SCHEMA }))
);
const ok = results.filter(Boolean);
const defects = ok.flatMap(r => (r.findings || []).filter(f => f.isDefect));
log(`Готово: ${ok.length}/${DATA.groups.length} глав, дефектов: ${defects.length}`);
return { results: ok };
"""

out = ROOT / "build" / "polish-audit.workflow.js"
out.write_text(HEADER + DATA + BODY, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes); групп={len(groups)}, кандидатов={len(cands)}")
