"""Генератор crypto-dukpt-provisioning.svg и crypto-dukpt-transaction.svg, гл. 10.

AES DUKPT по ANSI X9.24-3-2017 (ansi-x9-24-3): Initial Key из BDK
(provisioning) и Working Key из IDK (per-transaction). Значения ключей --
официальные векторы Supplement to X9.24-3-2017 (x9-24-3-test-vectors),
их же проверяет samples/ch10-dukpt/test_dukpt.py.

Поля derivation data кодируются тирами светлоты byte-map: служебные поля --
TIER_PANEL, keyUsage -- TIER_DARK, IKI -- TIER_NEUTRAL, counter -- TIER_LIGHT.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, ACCENT_B, CANVAS_W, FS_BODY, FS_HEAD, FS_NOTE, INK, MUTED, PANEL,
  SW_FRAME, TIER_DARK, TIER_LIGHT, TIER_NEUTRAL, arrow, box, figures_dir,
  markers, svg_header_pt, t, text_width, write_svg,
)

M = 2
W = CANVAS_W - 2 * M
KEY_H = 18
CELL_H = 18
BYTE_W = W / 16
AES_H = 16
ARROW_GAP = 12

BDK = "FE DC BA 98 76 54 32 10 F1 F1 F1 F1 F1 F1 F1 F1"
IKI = "12 34 56 78 90 12 34 56"
IK = "12 73 67 1E A2 6A C2 9A FA 4D 10 84 12 76 52 A1"
IDK = "4F 21 B5 65 BA D9 83 5E 11 2B 64 65 63 5E AE 44"
PEK = "AF 8C B1 33 A7 8F 8D C2 D1 35 9F 18 52 75 93 FB"
COUNTER = "00 00 00 01"

SERVICE = (PANEL, 1.0)
USAGE = (ACCENT_B, TIER_DARK)
IKI_T = (MUTED, TIER_NEUTRAL)
CNT_T = (ACCENT_A, TIER_LIGHT[0])


def dd(key_usage, tail):
  """Поля derivation data: (байт, значение, подпись, тон)."""
  return [
    (1, "01", "version", SERVICE),
    (1, "01", "cnt", SERVICE),
    (2, key_usage, "keyUsage", USAGE),
    (2, "00 02", "algo", SERVICE),
    (2, "00 80", "length", SERVICE),
  ] + tail


DD_INIT = dd("80 01", [(8, IKI, "IKI", IKI_T)])
DD_TX_TAIL = [(4, "90 12 34 56", "IKI[lo4]", IKI_T), (4, COUNTER, "counter", CNT_T)]
DD_IDK = dd("80 00", DD_TX_TAIL)
DD_WK = dd("10 00", DD_TX_TAIL)


def _fits(s, w, size=FS_BODY, weight="bold"):
  assert text_width(s, size, weight) < w, s


def key_row(y, label, value, size_note, tone=None):
  """Ключ одной строкой: имя слева, hex по центру, длина справа."""
  hx = M + W / 2 + 20
  _fits(label, hx - text_width(value, FS_BODY, "bold") / 2 - M - 8)
  return [
    "<g>",
    box(M, y, W, KEY_H, tone),
    t(M + 6, y + 12, label, size=FS_BODY, weight="bold", anchor="start"),
    t(hx, y + 12, value, size=FS_BODY, weight="bold"),
    t(M + W - 6, y + 12, size_note, size=FS_NOTE, fill=MUTED, anchor="end"),
    "</g>",
  ]


def dd_row(y, title, fields):
  """Заголовок, ячейки полей по байтам, подписи полей под ячейками."""
  out = [t(M, y + 8, title, size=FS_BODY, weight="bold", anchor="start"), "<g>"]
  y += 12
  x = M
  for nbytes, value, lbl, (fill, op) in fields:
    w = nbytes * BYTE_W
    _fits(value, w)
    opa = f' fill-opacity="{op}"' if op != 1.0 else ""
    out.append(
      f'<rect x="{x:.2f}" y="{y}" width="{w - 1:.2f}" height="{CELL_H}" '
      f'fill="{fill}"{opa} stroke="{MUTED}" stroke-width="{SW_FRAME}"/>'
    )
    cx = x + (w - 1) / 2
    out.append(t(f"{cx:.2f}", y + 12, value, size=FS_BODY, weight="bold"))
    out.append(t(f"{cx:.2f}", y + CELL_H + 8, lbl, size=FS_NOTE, fill=MUTED))
    x += w
  out.append("</g>")
  return out, y + CELL_H + 10


def aes_stage(y, tone_out="Muted"):
  """Стрелка, блок AES-128 ECB, стрелка; возвращает y следующего блока."""
  cx = M + W / 2
  out = [arrow(cx, y, cx, y + ARROW_GAP)]
  y += ARROW_GAP + 1
  out += [
    "<g>",
    box(M, y, W, AES_H),
    t(cx, y + 11, "AES-128 ECB", size=FS_BODY, weight="bold"),
    "</g>",
  ]
  y += AES_H
  out.append(arrow(cx, y, cx, y + ARROW_GAP, tone_out))
  return out, y + ARROW_GAP + 1


def header(y, s):
  return t(M, y, s, size=FS_HEAD, weight="bold", fill=MUTED, anchor="start")


def provisioning():
  body = [header(10, "Provisioning (один раз)")]
  y = 16
  body += key_row(y, "BDK", BDK, "16 B")
  y += KEY_H + 4
  body += key_row(y, "IKI", IKI, "8 B")
  y += KEY_H + 6
  rows, y = dd_row(y, "Derivation Data (16 B) для Initial Key", DD_INIT)
  body += rows
  rows, y = aes_stage(y)
  body += rows
  body += key_row(y, "Initial Key (IK)", IK, "16 B")
  h = y + KEY_H + M
  return svg_header_pt(CANVAS_W, h, markers("Muted")) + body + ["</svg>"]


def transaction():
  body = [header(10, "Per-transaction (counter = 0x00000001)")]
  y = 16
  kh = 28
  cw = 110
  body += [
    "<g>",
    box(M, y, cw, kh),
    t(M + cw / 2, y + 11, COUNTER, size=FS_BODY, weight="bold"),
    t(M + 6, y + 23, "Counter", size=FS_BODY, weight="bold", anchor="start"),
    "</g>",
  ]
  kx = M + cw + 6
  kw = W - cw - 6
  ksn = f"{IKI} {COUNTER}"
  body += [
    "<g>",
    box(kx, y, kw, kh),
    t(kx + kw / 2, y + 11, ksn, size=FS_BODY, weight="bold"),
    t(kx + 6, y + 23, "KSN = IKI ‖ counter", size=FS_BODY, weight="bold",
      anchor="start"),
    t(kx + kw - 6, y + 11, "12 B", size=FS_NOTE, fill=MUTED, anchor="end"),
    "</g>",
  ]
  y += kh + 6
  rows, y = dd_row(y, "Шаг 1. IK → IDK", DD_IDK)
  body += rows
  rows, y = aes_stage(y)
  body += rows
  body += key_row(y, "IDK", IDK, "16 B")
  y += KEY_H + 6
  rows, y = dd_row(y, "Шаг 2. IDK → Working Key (PIN / MAC / Data)", DD_WK)
  body += rows
  rows, y = aes_stage(y, "Good")
  body += rows
  body += key_row(y, "PIN Encryption Key", PEK, "16 B", tone="Good")
  h = y + KEY_H + M
  return svg_header_pt(CANVAS_W, h, markers("Muted", "Good")) + body + ["</svg>"]


if __name__ == "__main__":
  out = figures_dir() / "ch10-cryptography"
  write_svg(out / "crypto-dukpt-provisioning.svg", provisioning())
  write_svg(out / "crypto-dukpt-transaction.svg", transaction())
