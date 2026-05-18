"""
art/render_operational_silence.py
=================================
Generates `operational-silence.pdf` — a 3-page coffee-table art piece
embodying the Operational Silence philosophy.

Page composition:
    I.   DECLARATION   — a single severe numeral on void; clinical metadata.
    II.  REGISTER      — 501 identical marks in a regulated grid on aged paper.
    III. STELLAR INDEX — concentric chart of execution coordinates.

The references hide inside the marks:
    • The numeral on Page I is 66 set in Boldonse, treated like a cold seal.
    • Page II has 501 ticks (Vader's legion designation), nine slightly bolder
      to mark those who broke the conditioning.
    • Page III plots eleven coordinates that read like a star chart but
      correspond, for the initiated, to known galactic locations.

Run:
    cd "/home/cs/workspace/Destiny 2/destiny2-loadout-toolkit"
    python3 art/render_operational_silence.py
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ------------------------------------------------------------
# Output + fonts
# ------------------------------------------------------------
HERE = Path(__file__).parent
OUT = HERE / "operational-silence.pdf"
FONTS_DIR = Path("/home/cs/.claude/skills/canvas-design/canvas-fonts")

FONT_MAP = {
    # alias → (file, fallback)
    "Boldonse":        "Boldonse-Regular.ttf",
    "EricaOne":        "EricaOne-Regular.ttf",
    "BigShouldersBold":"BigShoulders-Bold.ttf",
    "BigShoulders":    "BigShoulders-Regular.ttf",
    "Italiana":        "Italiana-Regular.ttf",
    "InstrumentSerif": "InstrumentSerif-Regular.ttf",
    "InstrumentSerifItalic": "InstrumentSerif-Italic.ttf",
    "IBMMono":         "IBMPlexMono-Regular.ttf",
    "IBMMonoBold":     "IBMPlexMono-Bold.ttf",
    "DMMono":          "DMMono-Regular.ttf",
    "JuraLight":       "Jura-Light.ttf",
    "CrimsonPro":      "CrimsonPro-Regular.ttf",
    "CrimsonItalic":   "CrimsonPro-Italic.ttf",
    "Tektur":          "Tektur-Medium.ttf",
}
for alias, fname in FONT_MAP.items():
    pdfmetrics.registerFont(TTFont(alias, str(FONTS_DIR / fname)))

# ------------------------------------------------------------
# Palette  (three voices only — bone, ink, oxide)
# ------------------------------------------------------------
INK_DEEP   = HexColor("#0E0D0B")  # near-black with warm undertone
INK        = HexColor("#1B1916")
BONE       = HexColor("#EFE8D4")  # aged paper, slight ochre
BONE_DEEP  = HexColor("#E2D7BD")
OXIDE      = HexColor("#7A1015")  # dried blood
OXIDE_DIM  = HexColor("#5A0C10")
GRAPHITE   = HexColor("#3E3B36")
ASH        = HexColor("#8B847A")
GOLD       = HexColor("#9A7B3C")  # used at the absolute minimum

# Page geometry — slightly elongated (book proportion)
PAGE_W = 8.5 * inch
PAGE_H = 11.0 * inch
MARGIN = 0.75 * inch


# ============================================================
# Page I — DECLARATION
# Severe black ground. A single severe numeral floats in a regulated field.
# Three architectural zones — header, numeral, register — separated by
# hairline rules. Every element placed by measurement, never by impulse.
# ============================================================
def page_i(c: canvas.Canvas):
    # Solid void — the ground of consequence
    c.setFillColor(INK_DEEP)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Imperceptible paper grain so the flat field reads as material, not pixel
    import random
    rng = random.Random(66)
    c.setFillColor(Color(0.15, 0.13, 0.10, alpha=0.05))
    for _ in range(2200):
        x = rng.uniform(0, PAGE_W)
        y = rng.uniform(0, PAGE_H)
        r = rng.uniform(0.12, 0.36)
        c.circle(x, y, r, fill=1, stroke=0)

    # ----------------------------------------------------------
    # ZONE 1 — Header (top, ~1.0")
    # ----------------------------------------------------------
    header_y = PAGE_H - MARGIN
    c.setFillColor(BONE_DEEP)
    c.setFont("IBMMono", 7)
    c.drawString(MARGIN, header_y, "FILE")
    c.setFont("IBMMonoBold", 7)
    c.drawString(MARGIN + 28, header_y, "GAR · DIR · VI · OPERATIONAL")

    # Right-side classification stamp — restrained, hairline rule
    stamp_w = 1.6 * inch
    c.setStrokeColor(OXIDE)
    c.setLineWidth(0.5)
    sx = PAGE_W - MARGIN - stamp_w
    c.line(sx, header_y - 4, sx + stamp_w, header_y - 4)
    c.line(sx, header_y + 10, sx + stamp_w, header_y + 10)
    c.setFillColor(OXIDE)
    c.setFont("BigShouldersBold", 8)
    c.drawCentredString(sx + stamp_w / 2, header_y - 1,
                        "IMPERIAL EYES ONLY")

    # Hairline rule under header — defines the first zone
    rule_top_y = header_y - 0.42 * inch
    c.setStrokeColor(BONE_DEEP)
    c.setLineWidth(0.4)
    c.line(MARGIN, rule_top_y, PAGE_W - MARGIN, rule_top_y)
    # Two flanking short marks above the rule (an archival flourish)
    for x in (MARGIN, PAGE_W - MARGIN):
        c.line(x, rule_top_y, x, rule_top_y + 5)

    # ----------------------------------------------------------
    # ZONE 2 — The Numeral (centre)
    # Boldonse at 310pt. Glyphs touch with deliberate kerning.
    # Positioned so its baseline sits at the optical centre of the page.
    # ----------------------------------------------------------
    numeral_font = "Boldonse"
    size = 320
    c.setFont(numeral_font, size)
    glyph_w = c.stringWidth("66", numeral_font, size)
    nx = (PAGE_W - glyph_w) / 2
    # Vertical centring: place baseline so that the cap height (≈0.7*size)
    # straddles the optical centre of the page.
    optical_centre = PAGE_H / 2 + 0.10 * inch
    ny = optical_centre - size * 0.32
    c.setFillColor(OXIDE)
    c.drawString(nx, ny, "66")

    # A thin oxide hairline traces just beneath the numeral — like the
    # underline on an official seal.
    underline_y = ny - 0.30 * inch
    c.setStrokeColor(OXIDE_DIM)
    c.setLineWidth(0.6)
    c.line(PAGE_W / 2 - 0.9 * inch, underline_y, PAGE_W / 2 + 0.9 * inch, underline_y)

    # Tiny inscription centred beneath the rule — Latin-feel, archival
    c.setFillColor(BONE_DEEP)
    c.setFont("Italiana", 13)
    c.drawCentredString(PAGE_W / 2, underline_y - 0.30 * inch, "Operational Silence")
    c.setFillColor(ASH)
    c.setFont("IBMMono", 6.5)
    c.drawCentredString(PAGE_W / 2, underline_y - 0.50 * inch,
                        "A  R E G U L A T E D   F I E L D   O F   U N C O N T E S T E D   D E C I S I O N")

    # ----------------------------------------------------------
    # ZONE 3 — The Register (bottom)
    # Separated from the centre by another hairline rule. Three
    # designation pillars; an issuing-authority block on the right.
    # ----------------------------------------------------------
    rule_bottom_y = MARGIN + 1.3 * inch
    c.setStrokeColor(BONE_DEEP)
    c.setLineWidth(0.4)
    c.line(MARGIN, rule_bottom_y, PAGE_W - MARGIN, rule_bottom_y)
    for x in (MARGIN, PAGE_W - MARGIN):
        c.line(x, rule_bottom_y, x, rule_bottom_y - 5)

    # Issuing-authority block, RIGHT aligned, set tight in mono
    right_x = PAGE_W - MARGIN
    c.setFillColor(BONE_DEEP)
    c.setFont("IBMMono", 7)
    auth_lines = [
        ("ISSUED",        "19 BBY · 03·22"),
        ("JURISDICTION",  "GRAND ARMY · GAR"),
        ("STATUS",        "SEALED · ARCHIVED"),
        ("FOLIO",         "I  /  III"),
    ]
    for i, (k, v) in enumerate(auth_lines):
        y = rule_bottom_y - 0.32 * inch - i * 11
        c.setFillColor(ASH)
        c.drawRightString(right_x - 1.45 * inch, y, k)
        c.setFillColor(BONE_DEEP)
        c.drawRightString(right_x, y, v)

    # Three designation pillars, LEFT side
    pillar_y_top = rule_bottom_y - 0.32 * inch
    pillar_x = MARGIN
    pillars = [
        ("GAR · 501",  "VIZSLA"),
        ("CC · 2224",  "CODY"),
        ("CT · 7567",  "REX"),
    ]
    pillar_gap = 0.95 * inch
    c.setFillColor(BONE_DEEP)
    c.setFont("DMMono", 7.5)
    for i, (code, name) in enumerate(pillars):
        y_code = pillar_y_top - i * 0.22 * inch
        c.drawString(pillar_x, y_code, code)
        c.setFillColor(ASH)
        c.setFont("DMMono", 6.5)
        c.drawString(pillar_x + 0.85 * inch, y_code, name)
        c.setFillColor(BONE_DEEP)
        c.setFont("DMMono", 7.5)

    # ----------------------------------------------------------
    # Page number — set very small, painstakingly centred
    # ----------------------------------------------------------
    c.setFillColor(GRAPHITE)
    c.setFont("DMMono", 6.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 0.05 * inch, "—   I   —")


# ============================================================
# Page II — REGISTER
# Aged paper. 501 identical marks in a regulated grid.
# Nine struck through. The viewer counts, loses count, submits.
# ============================================================
def page_ii(c: canvas.Canvas):
    # Paper ground
    c.setFillColor(BONE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Paper grain — countless flecks
    import random
    rng = random.Random(501)
    c.setFillColor(Color(0.12, 0.10, 0.07, alpha=0.06))
    for _ in range(3200):
        x = rng.uniform(0, PAGE_W)
        y = rng.uniform(0, PAGE_H)
        r = rng.uniform(0.12, 0.38)
        c.circle(x, y, r, fill=1, stroke=0)

    # ---- top header block ----
    top_y = PAGE_H - MARGIN
    c.setFillColor(INK)
    c.setFont("IBMMonoBold", 7.5)
    c.drawString(MARGIN, top_y, "REGISTER · VI")
    c.setFillColor(GRAPHITE)
    c.setFont("IBMMono", 7.5)
    c.drawString(MARGIN + 86, top_y, "GAR / 501 LEGION / ROLL")

    c.setFillColor(OXIDE)
    c.setFont("DMMono", 7)
    c.drawRightString(PAGE_W - MARGIN, top_y, "501 · ENTRIES · 9 ANOMALIES")

    # hairline rule below header
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.4)
    c.line(MARGIN, top_y - 8, PAGE_W - MARGIN, top_y - 8)

    # ---- title ----
    c.setFillColor(INK)
    c.setFont("Italiana", 26)
    c.drawString(MARGIN, top_y - 0.55 * inch, "The Roll")
    c.setFillColor(GRAPHITE)
    c.setFont("CrimsonItalic", 11)
    c.drawString(MARGIN, top_y - 0.78 * inch,
                 "five hundred and one tally marks, of which nine refused.")

    # ---- the grid of 501 marks ----
    # Layout: 23 cols × 22 rows = 506 cells; we draw 501 marks
    cols = 23
    rows = 22
    grid_top = top_y - 1.30 * inch
    grid_bottom = MARGIN + 1.0 * inch
    grid_h = grid_top - grid_bottom
    grid_w = PAGE_W - 2 * MARGIN
    cell_w = grid_w / cols
    cell_h = grid_h / rows

    # 9 "anomalies" — the ones who refused the order, scattered deterministically
    anomaly_ids = {37, 92, 144, 211, 263, 308, 360, 422, 477}

    # Each mark: a short vertical tick + a horizontal hairline cap.
    # The anomalies are struck through (X) rather than ticked.
    for i in range(501):
        col = i % cols
        row = i // cols
        x_center = MARGIN + (col + 0.5) * cell_w
        y_center = grid_top - (row + 0.5) * cell_h

        if i in anomaly_ids:
            # Struck — small X in oxide
            c.setStrokeColor(OXIDE)
            c.setLineWidth(0.9)
            r = 3.4
            c.line(x_center - r, y_center - r, x_center + r, y_center + r)
            c.line(x_center - r, y_center + r, x_center + r, y_center - r)
        else:
            # Standard tally — short vertical stroke
            c.setStrokeColor(INK)
            c.setLineWidth(0.55)
            c.line(x_center, y_center - 3.6, x_center, y_center + 3.6)

    # column tick marks beneath grid
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.3)
    for col in range(cols + 1):
        x = MARGIN + col * cell_w
        c.line(x, grid_bottom - 0.05 * inch, x, grid_bottom + 0.0)

    # tiny column-index labels
    c.setFillColor(ASH)
    c.setFont("DMMono", 5.5)
    for col in range(0, cols, 4):
        x = MARGIN + (col + 0.5) * cell_w
        c.drawCentredString(x, grid_bottom - 0.16 * inch, f"{col + 1:02d}")

    # row-index labels on left
    for row in range(0, rows, 3):
        y = grid_top - (row + 0.5) * cell_h
        c.drawString(MARGIN - 0.32 * inch, y - 2, f"{row + 1:02d}")

    # ---- the footnote ----
    foot_y = MARGIN + 0.45 * inch
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.3)
    c.line(MARGIN, foot_y + 12, MARGIN + 1.8 * inch, foot_y + 12)

    c.setFillColor(INK)
    c.setFont("CrimsonItalic", 10)
    c.drawString(MARGIN, foot_y,
                 "of nine: who heard, & did not.")

    # right-aligned coda
    c.setFillColor(GRAPHITE)
    c.setFont("IBMMono", 7)
    c.drawRightString(PAGE_W - MARGIN, foot_y,
                      "CT-5597 · CC-1119 · ARC-77 · CT-411 · CT-7567 ·")
    c.drawRightString(PAGE_W - MARGIN, foot_y - 11,
                      "CC-3636 · CT-5555 · CT-782 · CC-1010")

    # page number
    c.setFillColor(GRAPHITE)
    c.setFont("DMMono", 6.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 0.1 * inch, "— II —")


# ============================================================
# Page III — STELLAR INDEX
# Aged paper. A circular chart of execution coordinates.
# Concentric rings, tick marks every five degrees, eleven plot points.
# The eleven, for the initiated, are the worlds of Order 66.
# ============================================================
def page_iii(c: canvas.Canvas):
    c.setFillColor(BONE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # paper grain
    import random
    rng = random.Random(11)
    c.setFillColor(Color(0.12, 0.10, 0.07, alpha=0.06))
    for _ in range(3000):
        x = rng.uniform(0, PAGE_W)
        y = rng.uniform(0, PAGE_H)
        r = rng.uniform(0.12, 0.38)
        c.circle(x, y, r, fill=1, stroke=0)

    # ---- header block ----
    top_y = PAGE_H - MARGIN
    c.setFillColor(INK)
    c.setFont("IBMMonoBold", 7.5)
    c.drawString(MARGIN, top_y, "STELLAR INDEX · XI")
    c.setFillColor(GRAPHITE)
    c.setFont("IBMMono", 7.5)
    c.drawString(MARGIN + 110, top_y, "GAR / DECLINATIONS")
    c.setFillColor(OXIDE)
    c.setFont("DMMono", 7)
    c.drawRightString(PAGE_W - MARGIN, top_y, "11 COORDINATES · ALL SEALED")
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.4)
    c.line(MARGIN, top_y - 8, PAGE_W - MARGIN, top_y - 8)

    # ---- title ----
    c.setFillColor(INK)
    c.setFont("Italiana", 26)
    c.drawString(MARGIN, top_y - 0.55 * inch, "The Chart")
    c.setFillColor(GRAPHITE)
    c.setFont("CrimsonItalic", 11)
    c.drawString(MARGIN, top_y - 0.78 * inch,
                 "eleven points, drawn precisely; no narrative supplied.")

    # ---- the concentric chart ----
    cx = PAGE_W / 2
    cy = MARGIN + 4.4 * inch
    R = 2.6 * inch

    # Outer rings
    c.setStrokeColor(GRAPHITE)
    for r, lw in [(R, 0.7), (R * 0.92, 0.3), (R * 0.62, 0.3), (R * 0.28, 0.3)]:
        c.setLineWidth(lw)
        c.circle(cx, cy, r, stroke=1, fill=0)

    # Hairline tick marks every 5° on the outer ring.
    # Cardinal positions (0/90/180/270) are reserved for the italic
    # words MERIDIAN/ANTIPODE/ASCENT/DESCENT, so we omit their numeric
    # labels to keep the composition clean.
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.25)
    cardinal = {0, 90, 180, 270}
    for deg in range(0, 360, 5):
        a = math.radians(deg)
        x1 = cx + (R + 2) * math.cos(a)
        y1 = cy + (R + 2) * math.sin(a)
        long_tick = (deg % 30 == 0)
        x2 = cx + (R + (8 if long_tick else 4)) * math.cos(a)
        y2 = cy + (R + (8 if long_tick else 4)) * math.sin(a)
        c.line(x1, y1, x2, y2)
        if long_tick and deg not in cardinal:
            c.setFillColor(ASH)
            c.setFont("DMMono", 6)
            label_r = R + 16
            lx = cx + label_r * math.cos(a)
            ly = cy + label_r * math.sin(a) - 2
            c.drawCentredString(lx, ly, f"{deg:03d}°")

    # Eleven plot points — placed at deterministic coordinates on inner rings.
    # The eleven, for those who know:
    #   Kashyyyk, Felucia, Saleucami, Mygeeto, Cato Neimoidia, Coruscant,
    #   Kaller, Mustafar, Utapau, Bracca, Murkhana.
    # Names are NOT shown — only their bearing and radius.
    points = [
        # (angle_deg, radial_fraction_of_R, label_id)
        (18,   0.82, "K-7"),
        (54,   0.61, "F-3"),
        (88,   0.74, "S-2"),
        (122,  0.43, "M-9"),
        (155,  0.78, "CN-4"),
        (180,  0.24, "·"),     # the centre body
        (212,  0.49, "K-1"),
        (243,  0.68, "M-1"),
        (276,  0.32, "U-8"),
        (310,  0.84, "B-6"),
        (342,  0.55, "M-5"),
    ]

    # Plot points
    for deg, rf, label in points:
        a = math.radians(deg)
        x = cx + R * rf * math.cos(a)
        y = cy + R * rf * math.sin(a)
        is_centre = (label == "·")
        # outer ring around the point
        c.setStrokeColor(OXIDE)
        c.setLineWidth(0.5)
        c.circle(x, y, 5 if is_centre else 4, stroke=1, fill=0)
        # solid centre
        c.setFillColor(OXIDE if not is_centre else INK)
        c.circle(x, y, 1.6 if is_centre else 1.4, stroke=0, fill=1)
        # leader line from point outward to a small index label
        if not is_centre:
            label_a = a
            x2 = cx + (R * rf + 18) * math.cos(label_a)
            y2 = cy + (R * rf + 18) * math.sin(label_a)
            c.setStrokeColor(GRAPHITE)
            c.setLineWidth(0.3)
            c.line(x + 5.5 * math.cos(label_a),
                   y + 5.5 * math.sin(label_a),
                   x2, y2)
            c.setFillColor(INK)
            c.setFont("DMMono", 6.5)
            c.drawCentredString(x2 + 8 * math.cos(label_a),
                                y2 + 8 * math.sin(label_a) - 2,
                                label)

    # Axis labels (cardinal) — set in serif italic for warmth against the geometry.
    # Positioned outside the numeric label radius so they sit in their own zone.
    c.setFillColor(GRAPHITE)
    c.setFont("CrimsonItalic", 10)
    c.drawCentredString(cx, cy + R + 30, "MERIDIAN")
    c.drawCentredString(cx, cy - R - 26, "ANTIPODE")
    c.drawString(cx + R + 30, cy - 3, "ASCENT")
    c.drawRightString(cx - R - 30, cy - 3, "DESCENT")

    # centre label
    c.setFillColor(INK)
    c.setFont("Italiana", 12)
    c.drawCentredString(cx, cy - R - 50, "—  ELEVEN  —")

    # ---- bottom block: legend + coda ----
    foot_y = MARGIN + 0.7 * inch
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.3)
    c.line(MARGIN, foot_y + 24, MARGIN + 1.6 * inch, foot_y + 24)

    c.setFillColor(INK)
    c.setFont("CrimsonItalic", 10)
    c.drawString(MARGIN, foot_y + 8,
                 "no narrative supplied;")
    c.drawString(MARGIN, foot_y - 4,
                 "let the geometry stand as evidence.")

    # right block — colophon
    c.setFillColor(GRAPHITE)
    c.setFont("IBMMono", 6.5)
    lines = [
        "PROJECTION   POLAR",
        "DATUM        GAR-19",
        "EPOCH        19 BBY · 03·22",
        "COMPILED BY  HAND",
    ]
    for i, ln in enumerate(lines):
        c.drawRightString(PAGE_W - MARGIN, foot_y + 14 - i * 10, ln)

    # page number
    c.setFillColor(GRAPHITE)
    c.setFont("DMMono", 6.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 0.1 * inch, "— III —")


# ============================================================
# Build
# ============================================================
def build():
    c = canvas.Canvas(
        str(OUT),
        pagesize=(PAGE_W, PAGE_H),
        pdfVersion=(1, 7),
    )
    c.setTitle("Operational Silence")
    c.setAuthor("·")
    c.setSubject("A study in regulated absence.")
    c.setCreator("Operational Silence — Folio I·III")

    page_i(c)
    c.showPage()
    page_ii(c)
    c.showPage()
    page_iii(c)
    c.showPage()

    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
