"""Генератор visa-direct-flow.svg для гл. 13 (Visa Direct: AFT и~OCT).

Авторизационный поток V.I.P. System по~разделу Visa Direct гл.~13,
источник visa-direct; клиринг BASE II на~фигуре не~показан.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import re

from _common import FS_NOTE, MUTED, figures_dir, t, text_width, write_svg
from _seq import Act, Msg, Party, Phase, sequence

NOTIFY = "уведомление получателю"
DELAY = "T+минуты"

PARTIES = [
  Party("acq", "Банк-эквайер", "отправителя", side="AccentA"),
  Party("vn", "VisaNet", "V.I.P. System / BASE I"),
  Party("iss", "Банк-эмитент", "получателя", side="AccentB"),
]

EVENTS = [
  Phase("A. AFT — авторизация дебета отправителя"),
  Msg("acq", "vn", "AFT 0100 (снять у отправителя)"),
  Msg("vn", "acq", "Ответ AFT 0110 — авторизация OK", reply=True),
  Phase("B. OCT — перевод средств на карту получателя"),
  Msg("vn", "iss", "OCT 0200 (кредит получателю)"),
  Msg("iss", "vn", "Ответ OCT 0210", reply=True),
  Act("iss", NOTIFY),
]

if __name__ == "__main__":
  out = figures_dir() / "ch13-visa" / "visa-direct-flow.svg"
  svg = sequence(PARTIES, EVENTS)
  # _seq.Act не несёт пометки: задержка ставится слева от блока уведомления.
  i = next(i for i, e in enumerate(svg) if e.startswith("<text") and NOTIFY in e)
  x = float(re.search(r'x="([\d.]+)"', svg[i]).group(1))
  y = float(re.search(r'y="([\d.]+)"', svg[i]).group(1))
  left = x - (text_width(NOTIFY, FS_NOTE, "bold") + 10) / 2
  svg.insert(i + 1, t(f"{left - 4:.1f}", y, DELAY, size=FS_NOTE, fill=MUTED,
                      anchor="end"))
  write_svg(out, svg)
