#!/usr/bin/env python3
"""Round-2 workflow: триаж кандидатов «пустых мест» (vision).
Каждый агент смотрит p-1/p/p+1, читает исходник главы, решает defect vs normal,
предлагает минимальный фикс. Самосборку не запускает."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cands = set(json.loads((ROOT / "build" / "whitespace-candidates.json").read_text()))
cands |= {334}  # gap-кандидат, не попавший в bottom-список
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))


def unit_of(p):
    for u in manifest:
        if u["first_page"] <= p <= u["last_page"]:
            return u
    return None


items = []
for p in sorted(cands):
    u = unit_of(p)
    if not u:
        continue
    tex = u["tex"]
    items.append({
        "page": p, "key": u["key"],
        "tex": (tex if isinstance(tex, str) else (tex[0] if tex else None)),
        "first": u["first_page"], "last": u["last_page"],
        "is_chapter_end": p == u["last_page"],
    })

HEADER = (
    "export const meta = {\n"
    "  name: 'reflow-round2-whitespace',\n"
    "  description: 'Round-2 триаж пустот/разрывов на странице (defect vs штатная вёрстка)',\n"
    "  phases: [ { title: 'Triage', detail: 'классификация кандидатов пустот по страницам' } ],\n"
    "}\n\n"
)
DATA = "const ITEMS = " + json.dumps(items, ensure_ascii=False) + ";\n\n"

BODY = r"""
const PNG = 'build/page-pngs/all';
const pad = n => 'p' + String(n).padStart(3, '0') + '.png';

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    page: { type: 'integer' },
    verdict: { type: 'string', enum: ['defect', 'normal'] },
    severity: { type: 'string', enum: ['high', 'medium', 'low', 'none'] },
    cause: { type: 'string' },
    fix: { type: 'string' },
    target: { type: 'string' },
  },
  required: ['page', 'verdict', 'severity', 'cause', 'fix', 'target'],
};

function prompt(it) {
  const imgs = [it.page - 1, it.page, it.page + 1]
    .filter(p => p >= 1 && p <= 380)
    .map(p => `  ${PNG}/${pad(p)}`);
  return [
    'Ты — типографский корректор финальной вычитки книги «Инженерия платежей» (печать).',
    `Детектор отметил ВОЗМОЖНУЮ пустоту на печатной странице ${it.page}.`,
    `Это раздел ${it.key} (печ. стр. ${it.first}–${it.last}); исходник: ${it.tex}.`,
    it.is_chapter_end ? 'NB: это последняя страница главы — короткая полоса тут часто штатна.' : '',
    '',
    'Посмотри страницы (предыдущая / целевая / следующая):',
    ...imgs,
    '',
    'Реши, ДЕФЕКТ ли это или ШТАТНАЯ вёрстка. ШТАТНО (verdict=normal): конец главы;',
    'конец раздела с подвёрстанной снизу сноской; намеренная страница-флоат, целиком занятая',
    'крупной фигурой/таблицей; титульные/оборотные полосы (front/back matter); глоссарий/список',
    'источников с рваным низом колонки. ДЕФЕКТ (verdict=defect): дыра ВНУТРИ полосы или большой',
    'нижний провал из-за того, что заголовок+первый абзац следующего раздела целиком вытолкнуты',
    'на следующую полосу; фигура/таблица с [H] не влезла и оставила провал; преждевременный',
    '\\needspace/\\pagebreak/\\FloatBarrier выбросил контент.',
    '',
    'Если ДЕФЕКТ — открой исходник, найди причину у границы полосы и предложи МИНИМАЛЬНУЮ правку',
    '(ослабить размещение флоата [H]→[!htbp]/[t]; уменьшить/снять \\needspace; снять \\pagebreak;',
    'перенести якорь фигуры выше, чтобы текст подтянулся). НЕ режь содержание, НЕ переписывай прозу,',
    'НЕ трогай размер фигуры без нужды. Укажи target (файл) и конкретное место (строка/окружение).',
    `Верни {page:${it.page}, verdict, severity, cause, fix, target}. Для normal: severity="none", fix="".`,
  ].filter(Boolean).join('\n');
}

phase('Triage');
log(`Round-2: триаж ${ITEMS.length} кандидатов пустот`);
const res = (await parallel(ITEMS.map(it => () =>
  agent(prompt(it), { label: `ws:p${it.page}`, phase: 'Triage', schema: SCHEMA })
))).filter(Boolean);

const defects = res.filter(r => r.verdict === 'defect');
log(`Готово: ${res.length} проверено, ${defects.length} дефектов`);
return { results: res, defects };
"""

out = ROOT / "build" / "reflow-round2.workflow.js"
out.write_text(HEADER + DATA + BODY, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes); candidates={len(items)}")
print("pages:", [it["page"] for it in items])
