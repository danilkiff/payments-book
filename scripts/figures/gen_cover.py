#!/usr/bin/env python3
"""Генератор векторной обложки книги → src/frontmatter/cover.tex.

Обложка (B5, full-bleed, 17.6×25 см): гиперкуб-тессеракт (16 вершин, 32 ребра,
4D→3D→2D с перспективой «cube-in-cube», глубинное затухание рёбер + узлы)
градиентом стальной→чернильный синий слева-направо; сплошной чернильно-синий
титул «ИНЖЕНЕРИЯ ПЛАТЕЖЕЙ» во всю ширину полосы; бледная чертёжная сетка
(blueprint); мягкие синие mesh-пятна по углам (та же пастель, что у открывателей
частей, но в синей гамме). Палитра намеренно холодная сине-стальная.

Запуск: python3 scripts/figures/gen_cover.py
Результат коммитится; руками cover.tex не править — менять этот скрипт.
"""
import math
from pathlib import Path

# ---------- геометрия тессеракта ----------
verts4 = [(x, y, z, w) for x in (-1, 1) for y in (-1, 1)
          for z in (-1, 1) for w in (-1, 1)]
def ham(a, b): return sum(1 for i in range(4) if a[i] != b[i])
edges = [(i, j) for i in range(16) for j in range(i + 1, 16)
         if ham(verts4[i], verts4[j]) == 1]  # 32 ребра

def rot4(v, axw, ayz):
    x, y, z, w = v
    return (x*math.cos(axw)-w*math.sin(axw), y*math.cos(ayz)-z*math.sin(ayz),
            y*math.sin(ayz)+z*math.cos(ayz), x*math.sin(axw)+w*math.cos(axw))
def proj43(v, d=3.2):
    x, y, z, w = v; s = 1.0/(d-w); return (x*s, y*s, z*s)
def rot3(v, ay, ax):
    x, y, z = v
    x2 = x*math.cos(ay)+z*math.sin(ay); z2 = -x*math.sin(ay)+z*math.cos(ay)
    return (x2, y*math.cos(ax)-z2*math.sin(ax), y*math.sin(ax)+z2*math.cos(ax))
def proj32(v, d=6.5):
    x, y, z = v; s = d/(d-z); return (x*s, y*s, z)

pts = []
for v in verts4:
    v = rot4(v, 0.32, 0.20); v = proj43(v, 3.2); v = rot3(v, 0.62, -0.40)
    pts.append(proj32(v, 6.5))
m = max(max(abs(p[0]) for p in pts), max(abs(p[1]) for p in pts))
norm = [(p[0]/m, p[1]/m, p[2]) for p in pts]
zs = [p[2] for p in pts]; zmin, zmax = min(zs), max(zs)
def near(z): return (z-zmin)/(zmax-zmin)   # 0 дальняя .. 1 ближняя
def tx(i): return (norm[i][0]+1)/2         # 0 слева .. 1 справа

MINOP = 0.34   # минимальная непрозрачность дальних рёбер

def placetess():
    out = ["\\newcommand{\\coverplacetess}[3]{%  #1 cx  #2 cy  #3 scale (см)"]
    for i, (nx, ny, _) in enumerate(norm):
        out.append(f"  \\coordinate (cv{i}) at "
                   f"({{#1+#3*({nx:.4f})}},{{#2+#3*({ny:.4f})}});")
    return "\n".join(out) + "%\n}"

def drawtess():
    ed = sorted(edges, key=lambda e: (near(pts[e[0]][2]) + near(pts[e[1]][2])) / 2)
    out = ["\\newcommand{\\coverdrawtess}{%"]
    for a, b in ed:
        d = (near(pts[a][2]) + near(pts[b][2])) / 2
        w = 0.45 + 0.70*d; op = MINOP + (1-MINOP)*d; P = round((tx(a)+tx(b))/2*100)
        out.append(f"  \\draw[draw=CoverGradHi!{P}!CoverGradLo,line cap=round,"
                   f"line join=round,line width={w:.2f}pt,opacity={op:.2f}] "
                   f"(cv{a})--(cv{b});")
    for i in range(16):
        d = near(pts[i][2]); op = MINOP + (1-MINOP)*d; P = round(tx(i)*100)
        out.append(f"  \\fill[CoverGradHi!{P}!CoverGradLo,opacity={op:.2f}] "
                   f"(cv{i}) circle ({0.030+0.022*d:.3f});")
    return "\n".join(out) + "%\n}"

SUB = "Открытая книга о карточных платежах, СБП и платёжной инфраструктуре"

BODY = r"""
\newcommand{\drawbookcover}{%
  \begin{tikzpicture}
    \useasboundingbox (0,0) rectangle (17.6,25);
    \clip (0,0) rectangle (17.6,25);
    \fill[white] (0,0) rectangle (17.6,25);
    % чертёжная сетка (blueprint): тонкая 1 см + усиленная 5 см, чернилами
    \draw[CoverInk,line width=0.2pt,opacity=0.05,step=1cm] (0,0) grid (17.6,25);
    \draw[CoverInk,line width=0.4pt,opacity=0.09,step=5cm] (0,0) grid (17.6,25);
    % мягкие синие mesh-пятна по углам
    \fill[CoverBloomA,path fading=coverbloom] (15.2,22.0) circle (8.0);
    \fill[CoverBloomB,path fading=coverbloom] (1.8,3.5) circle (8.5);
    \fill[CoverBloomC,path fading=coverbloom] (16.6,10.5) circle (5.5);
    % гиперкуб: стальной (слева) → чернильный (справа)
    \colorlet{CoverGradLo}{CoverSteel}\colorlet{CoverGradHi}{CoverInk}%
    \coverplacetess{8.8}{16.7}{4.2}
    \coverdrawtess
    % угловые реперные метки
    \begin{scope}[draw=CoverInk!55,line width=0.5pt,opacity=0.85]
      \draw (0.85,0.85)--+(0.5,0); \draw (0.85,0.85)--+(0,0.5);
      \draw (16.75,0.85)--+(-0.5,0); \draw (16.75,0.85)--+(0,0.5);
      \draw (0.85,24.15)--+(0.5,0); \draw (0.85,24.15)--+(0,-0.5);
      \draw (16.75,24.15)--+(-0.5,0); \draw (16.75,24.15)--+(0,-0.5);
    \end{scope}
    % верхняя метка
    \node[anchor=center,text=CoverInk!70,font=\sffamily] at (8.8,23.7) {\fontsize{9}{9}\selectfont O\kern0.22em P\kern0.22em E\kern0.22em N\kern0.22em \kern0.22em S\kern0.22em O\kern0.22em U\kern0.22em R\kern0.22em C\kern0.22em E};
    % титул во всю ширину полосы (сплошной чернильный синий)
    \node[anchor=center] at (8.8,7.3) {\resizebox{15.8cm}{!}{\sffamily\bfseries\color{CoverInk}ИНЖЕНЕРИЯ ПЛАТЕЖЕЙ}};
    % подзаголовок
    \node[anchor=center,text=CoverInk!82,font=\sffamily,align=center,text width=15cm] at (8.8,5.6) {\fontsize{11}{15}\selectfont SUBTEXT};
    % год
    \node[anchor=center,text=CoverInk!70,font=\sffamily\bfseries] at (8.8,1.45) {\fontsize{11}{11}\selectfont 2026};
  \end{tikzpicture}%
}
""".replace("SUBTEXT", SUB)

HEADER = r"""% AUTO-GENERATED by scripts/figures/gen_cover.py — DO NOT EDIT BY HAND.
% Перегенерировать: python3 scripts/figures/gen_cover.py
% Векторная обложка книги (B5, full-bleed). Подключается в src/preamble.tex
% (после src/styles, где загружены tikz+fadings); рисуется \drawbookcover
% из \makebookcover (src/frontmatter/pre.tex). Опирается на уже загруженные
% tikz, tikzlibrary fadings, graphicx, eso-pic, paratype.
%
% Палитра намеренно холодная сине-стальная: чернильный синий +
% стальной синий; mesh-пятна — синяя пастель (родня открывателям частей).
\definecolor{CoverInk}{HTML}{0C2236}     % чернильный синий (тёмный конец)
\definecolor{CoverSteel}{HTML}{2F6E95}   % стальной синий (светлый конец)
\definecolor{CoverBloomA}{HTML}{CFE0F1}  % mesh: светлый стальной
\definecolor{CoverBloomB}{HTML}{DDE9F5}  % mesh: бледнее
\definecolor{CoverBloomC}{HTML}{BFD4E9}  % mesh: глубже
\tikzfading[name=coverbloom, inner color=transparent!8, outer color=transparent!100]

"""

out = HEADER + placetess() + "\n\n" + drawtess() + "\n" + BODY
dest = Path(__file__).resolve().parent.parent.parent / "src" / "frontmatter" / "cover.tex"
dest.write_text(out, encoding="utf-8")
print(f"wrote {dest} — {len(edges)} edges, 16 verts")
