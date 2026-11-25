#!/usr/bin/env python3
"""The Daily Globe -- Wednesday, 25 November 2026.

A program that draws one newspaper front page summing up five stories
first reported (or happening) on 25 November 2026, and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Pure Python 3.13 standard library. No network, no files read, no clock,
no randomness with a hidden seed: the same run always writes the same
bytes. Everything on the page -- masthead, five drawn scenes, captions --
is produced by the drawing code below, including a small 5x7 bitmap font
defined by hand in this file.

The five stories (each checked against its first publication):
  1. Shenzhou-24 launches from Jiuquan; a Pakistani astronaut flies to
     Tiangong, the first foreign astronaut on China's station (Xinhua,
     China Daily, People's Daily, 25 Nov 2026).
  2. Australia and Solomon Islands sign a security treaty in Canberra;
     Honiara drops its 2022 security pact with China (Reuters, the
     Australian Prime Minister's office, 25 Nov 2026).
  3. The CIA and the US Office of the Director of National Intelligence
     suffer a breach of unclassified systems (New York Times first
     report; CNN, 24 Nov US time = 25 Nov in Asia-Pacific, carried in
     The Hindu's morning digest of 25 Nov 2026).
  4. Vladimir Putin holds talks in Moscow with the Sultan of Brunei,
     Hassanal Bolkiah, on a state visit (Kremlin announcement; the
     talks take place on 25 Nov 2026).
  5. The US Army carries out a controlled detonation of more than four
     tonnes of unstable lead azide at the Iowa Army Ammunition Plant
     on Wednesday morning (US Army advisory; detonation on 25 Nov 2026).
"""

import hashlib
import math
import os
import struct
import sys
import zlib

_cos = math.cos
_sin = math.sin

W = 1024
H = 1024

PAPER = (245, 239, 221)
INK = (20, 20, 20)
NAVY = (16, 32, 64)
RULE = (120, 110, 90)

# ---------------------------------------------------------------- font --
# A 5x7 bitmap font, drawn by hand. Each glyph is seven rows of five
# characters; '#' is ink, '.' is blank. Only the characters the page
# actually uses are defined; anything else renders as a blank.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (1px gap per glyph)."""
    return len(text) * (6 * scale) - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------- canvas --
class Canvas:
    """An RGB pixel buffer with small drawing primitives."""

    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.buf = bytearray(colour[0:1] * 0)  # replaced below
        row = bytes(colour) * width
        self.buf = bytearray(row * height)

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.buf[o] = colour[0]
            self.buf[o + 1] = colour[1]
            self.buf[o + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        span = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.buf[o:o + len(span)] = span

    def hline(self, x, y, w, colour):
        self.fill_rect(x, y, w, 1, colour)

    def vline(self, x, y, h, colour):
        self.fill_rect(x, y, 1, h, colour)

    def line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set_px(x, y, colour)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, colour, filled=True):
        if r <= 0:
            return
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            half = int((r * r - dy * dy) ** 0.5)
            if filled:
                self.fill_rect(cx - half, yy, half * 2 + 1, 1, colour)
            else:
                self.set_px(cx - half, yy, colour)
                self.set_px(cx + half, yy, colour)

    def triangle(self, ax, ay, bx, by, cx, cy, colour):
        # Scanline fill of a triangle, top to bottom.
        pts = sorted([(ax, ay), (bx, by), (cx, cy)], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        for y in range(y0, y2 + 1):
            xs = []
            for (px, py), (qx, qy) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x0, y0), (x2, y2))):
                if py == qy:
                    continue
                if min(py, qy) <= y <= max(py, qy):
                    t = (y - py) / (qy - py)
                    xs.append(px + t * (qx - px))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.fill_rect(xa, y, xb - xa + 1, 1, colour)

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient, one flat row at a time (fast, exact)."""
        if h <= 1:
            self.fill_rect(x, y, w, h, top)
            return
        for i in range(h):
            t = i / (h - 1)
            c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
            self.fill_rect(x, y + i, w, 1, c)

    def text(self, x, y, s, scale, colour):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for gy in range(7):
                row = glyph[gy]
                for gx in range(5):
                    if row[gx] == "1":
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       scale, scale, colour)
            cx += 6 * scale

    def text_centred(self, cx, y, s, scale, colour):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, colour)

    def stamp(self, x, y, w, h, border, colour):
        """A bordered stamp box (used for the UNCLASSIFIED / BREACH tags)."""
        for i in range(border):
            self.fill_rect(x + i, y + i, w - 2 * i, 1, colour)
            self.fill_rect(x + i, y + h - 1 - i, w - 2 * i, 1, colour)
            self.fill_rect(x + i, y, 1, h, colour)
            self.fill_rect(x + w - 1 - i, y, 1, h, colour)



# ---------------------------------------------------------------- png --
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ------------------------------------------------------------ helpers --
def hash01(i, salt):
    """Deterministic pseudo-random float in [0, 1) from an index."""
    v = (i * 2654435761 + salt * 40503) & 0xFFFFFFFF
    v ^= v >> 13
    v = (v * 1274126177) & 0xFFFFFFFF
    v ^= v >> 16
    return (v & 0xFFFFFF) / 16777216.0


def dashed_line(cv, x0, y0, x1, y1, colour, dash=10, gap=6):
    steps = max(abs(x1 - x0), abs(y1 - y0))
    if steps == 0:
        return
    on = True
    run = 0
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        if on:
            cv.set_px(x, y, colour)
            cv.set_px(x, y + 1, colour)
        run += 1
        if (on and run >= dash) or (not on and run >= gap):
            on = not on
            run = 0


def caption(cv, x, y, w, h, headline, sub, head_scale=2, sub_scale=1):
    """Dark caption strip with a headline line and a smaller sub-line."""
    cv.fill_rect(x, y, w, h, NAVY)
    cv.hline(x, y, w, (212, 175, 55))
    lines = wrap_text(headline, head_scale, w - 24)
    cy = y + 10
    for line in lines:
        cv.text(x + 12, cy, line, head_scale, (255, 255, 255))
        cy += 7 * head_scale + 4
    if sub:
        sub_lines = wrap_text(sub, sub_scale, w - 24)
        for line in sub_lines:
            cv.text(x + 12, cy + 2, line, sub_scale, (198, 205, 220))
            cy += 7 * sub_scale + 3


# ------------------------------------------------------------- scenes --
def draw_rocket(cv, x, y, w, h):
    """Shenzhou-24 lifts off at dawn from Jiuquan (hero panel)."""
    cv.vgrad(x, y, w, h, (8, 12, 40), (38, 62, 120))
    # Low sun glow near the horizon.
    cv.circle(x + int(w * 0.78), y + h - 120, 46, (232, 130, 58))
    cv.circle(x + int(w * 0.78), y + h - 120, 34, (244, 170, 90))
    # Stars, fixed positions from the hash helper.
    for i in range(110):
        sx = x + int(hash01(i, 11) * w)
        sy = y + int(hash01(i, 23) * (h * 0.55))
        bright = 200 if hash01(i, 31) > 0.6 else 140
        cv.set_px(sx, sy, (bright, bright, bright))
        if hash01(i, 47) > 0.85:
            cv.set_px(sx + 1, sy, (bright, bright, bright))
    # Tiangong station, top right: core module and solar wings.
    tx, ty = x + int(w * 0.66), y + 34
    cv.fill_rect(tx, ty + 8, 92, 14, (180, 190, 205))
    cv.fill_rect(tx + 34, ty, 24, 30, (210, 215, 225))
    cv.fill_rect(tx - 52, ty + 10, 52, 8, (40, 90, 170))
    cv.fill_rect(tx + 92, ty + 10, 52, 8, (40, 90, 170))
    cv.fill_rect(tx + 40, ty + 30, 12, 10, (150, 160, 175))
    cv.text(tx - 8, ty + 46, "TIANGONG", 1, (200, 210, 225))
    # Geometry of the stack, all relative to the panel.
    ground_h = 34
    base = y + h - ground_h          # pad level
    body_top = y + 92
    body_bottom = y + 210
    rx = x + int(w * 0.40)
    # Launch tower, left of the rocket, arms reaching to the body.
    tower_x = rx - 96
    cv.fill_rect(tower_x, y + 64, 26, base - (y + 64), (70, 76, 88))
    for arm_y in range(y + 104, body_bottom - 8, 40):
        cv.fill_rect(tower_x + 26, arm_y, 43, 6, (70, 76, 88))
    cv.fill_rect(tower_x - 6, y + 56, 38, 10, (90, 96, 108))
    # Ground and pad.
    cv.fill_rect(x, base, w, ground_h, (24, 26, 30))
    cv.fill_rect(rx - 70, base - 8, 140, 10, (60, 62, 66))
    # Smoke billowing at the base, drawn before the flame.
    for i in range(16):
        sx = rx - 120 + int(hash01(i, 71) * 240)
        sy = base - 14 + int(hash01(i, 83) * 22)
        r = 10 + int(hash01(i, 97) * 10)
        cv.circle(sx, sy, r, (150, 150, 148))
    # Flame: layered triangles, apex at the nozzle, wide at the pad.
    cv.triangle(rx - 36, base, rx + 36, base, rx, body_bottom + 4,
                (240, 110, 20))
    cv.triangle(rx - 24, base, rx + 24, base, rx, body_bottom + 4,
                (250, 190, 40))
    cv.triangle(rx - 12, base, rx + 12, base, rx, body_bottom + 4,
                (255, 240, 180))
    # Rocket body: tall white cylinder, red nose, blue window band.
    cv.fill_rect(rx - 27, body_top, 54, body_bottom - body_top,
                 (235, 238, 242))
    cv.fill_rect(rx - 27, body_bottom - 24, 54, 24, (200, 40, 40))
    cv.triangle(rx - 27, body_top, rx + 27, body_top, rx, body_top - 58,
                (200, 40, 40))
    cv.circle(rx, body_top + 52, 13, (30, 90, 160))
    cv.circle(rx, body_top + 52, 8, (140, 200, 240))
    cv.fill_rect(rx - 27, body_top + 84, 54, 8, (30, 90, 160))
    # Fins at the base of the body.
    cv.triangle(rx - 27, body_bottom - 24, rx - 27, body_bottom,
                rx - 53, body_bottom, (200, 40, 40))
    cv.triangle(rx + 27, body_bottom - 24, rx + 27, body_bottom,
                rx + 53, body_bottom, (200, 40, 40))


def draw_treaty(cv, x, y, w, h):
    """Pacific treaty: Australia, the Solomons, and a signed page."""
    cv.vgrad(x, y, w, h, (14, 90, 140), (10, 60, 100))
    # Sunlit sea sparkle.
    for i in range(40):
        sx = x + int(hash01(i, 5) * w)
        sy = y + int(h * 0.45 + hash01(i, 9) * h * 0.5)
        cv.set_px(sx, sy, (150, 210, 235))
        cv.set_px(sx + 1, sy, (150, 210, 235))
    # Australia: a sandy landmass, bottom left.
    ax, ay = x + 66, y + h - 58
    cv.circle(ax, ay, 40, (214, 178, 120))
    cv.circle(ax + 42, ay - 6, 30, (214, 178, 120))
    cv.circle(ax + 74, ay + 6, 20, (214, 178, 120))
    cv.circle(ax + 26, ay - 26, 22, (222, 190, 132))
    cv.text(ax - 22, ay - 4, "AUSTRALIA", 1, (90, 60, 20))
    # Solomon Islands: a chain of green isles, top right.
    for i in range(6):
        ix = x + w - 168 + i * 26
        iy = y + 30 + int(hash01(i, 13) * 20)
        cv.circle(ix, iy, 8 - (i % 2), (46, 140, 80))
    cv.text(x + w - 140, y + 64, "SOLOMONS", 1, (220, 235, 225))
    # Dashed treaty route between the two.
    dashed_line(cv, ax + 88, ay - 24, x + w - 150, y + 42, (255, 255, 255))
    # The signed treaty page, centre.
    px, py = x + w // 2 - 40, y + 14
    cv.fill_rect(px, py, 120, 100, (250, 248, 240))
    cv.fill_rect(px, py, 120, 5, (180, 30, 30))
    for i in range(5):
        cv.fill_rect(px + 12, py + 18 + i * 12, 96 - i * 6, 3,
                     (120, 120, 115))
    cv.circle(px + 88, py + 78, 12, (180, 30, 30))
    cv.circle(px + 88, py + 78, 7, (210, 70, 70))
    cv.text(px + 12, py + 82, "SIGNED", 1, (180, 30, 30))
    # Small flags: Australia bottom left, Solomons top right corner.
    cv.fill_rect(x + 10, y + h - 30, 40, 24, (20, 50, 130))
    cv.fill_rect(x + 10, y + h - 30, 40, 5, (255, 255, 255))
    cv.fill_rect(x + w - 52, y + h - 30, 40, 24, (20, 90, 160))
    cv.fill_rect(x + w - 52, y + h - 18, 40, 12, (30, 140, 70))


def draw_cyber(cv, x, y, w, h):
    """A breached server room: racks, a broken padlock, a red stamp."""
    cv.fill_rect(x, y, w, h, (10, 16, 24))
    # Falling binary digits, fixed positions.
    for i in range(46):
        bx = x + int(hash01(i, 17) * w)
        by = y + int(hash01(i, 19) * h)
        cv.text(bx, by, "1" if hash01(i, 29) > 0.5 else "0", 1,
                (40, 120, 90) if hash01(i, 37) > 0.7 else (24, 70, 52))
    # Server racks along the back.
    for rack in range(3):
        rx = x + 18 + rack * 62
        cv.fill_rect(rx, y + 22, 52, h - 44, (26, 34, 44))
        for row in range(6):
            ry = y + 32 + row * 16
            cv.fill_rect(rx + 6, ry, 40, 9, (16, 22, 30))
            for lamp in range(4):
                on = hash01(rack * 10 + row * 4 + lamp, 41) > 0.45
                cv.set_px(rx + 10 + lamp * 9, ry + 4,
                          (80, 220, 120) if on else (200, 60, 40))
                cv.set_px(rx + 11 + lamp * 9, ry + 4,
                          (80, 220, 120) if on else (200, 60, 40))
    # Padlock, centre right: brass body, rectangular broken shackle.
    lx, ly = x + w - 210, y + h // 2 - 62
    cv.fill_rect(lx + 16, ly + 2, 8, 42, (190, 160, 60))
    cv.fill_rect(lx + 72, ly + 2, 8, 42, (190, 160, 60))
    cv.fill_rect(lx + 16, ly - 6, 64, 10, (190, 160, 60))
    cv.fill_rect(lx, ly + 44, 96, 74, (200, 170, 60))
    cv.fill_rect(lx + 8, ly + 52, 80, 58, (180, 148, 46))
    cv.circle(lx + 48, ly + 82, 12, (30, 26, 18))
    cv.fill_rect(lx + 44, ly + 82, 8, 26, (30, 26, 18))
    # Red crack across the lock.
    cv.line(lx + 6, ly + 50, lx + 46, ly + 84, (200, 30, 30))
    cv.line(lx + 46, ly + 84, lx + 30, ly + 112, (200, 30, 30))
    # BREACH stamp, bottom left of the scene.
    sx, sy = x + 18, y + h - 78
    cv.stamp(sx, sy, 150, 44, 3, (220, 40, 40))
    cv.text(sx + 16, sy + 12, "BREACH", 3, (220, 40, 40))


def draw_summit(cv, x, y, w, h):
    """Moscow: a Kremlin tower on one side, a golden dome on the other."""
    cv.vgrad(x, y, w, h, (70, 24, 30), (140, 60, 44))
    # Pale winter sky band and snow line.
    cv.fill_rect(x, y, w, 30, (210, 200, 185))
    cv.fill_rect(x, y + h - 14, w, 14, (225, 222, 210))
    # Kremlin tower, left: body, roof, gold star, windows.
    kx = x + 40
    cv.fill_rect(kx, y + 40, 60, h - 54, (158, 32, 28))
    cv.fill_rect(kx - 6, y + 58, 72, 6, (120, 22, 20))
    cv.triangle(kx - 4, y + 40, kx + 64, y + 40, kx + 30, y + 14,
                (28, 110, 60))
    cv.circle(kx + 30, y + 10, 5, (230, 190, 60))
    cv.fill_rect(kx + 22, y + 66, 16, 14, (30, 22, 18))
    # Golden dome, right (Brunei).
    dx = x + w - 118
    cv.fill_rect(dx, y + 56, 76, h - 70, (240, 228, 200))
    cv.circle(dx + 38, y + 56, 36, (212, 175, 55))
    cv.circle(dx + 38, y + 56, 25, (232, 200, 90))
    cv.fill_rect(dx + 34, y + 16, 8, 10, (212, 175, 55))
    cv.circle(dx + 38, y + 12, 5, (212, 175, 55))
    cv.fill_rect(dx + 18, y + 72, 12, 14, (40, 90, 70))
    cv.fill_rect(dx + 48, y + 72, 12, 14, (40, 90, 70))
    # Two flags on poles, centre.
    for i, stripes in enumerate((((220, 220, 220), (30, 80, 180),
                                  (200, 40, 40)),
                                 ((250, 210, 40), (20, 20, 20),
                                  (250, 210, 40)))):
        fx = x + w // 2 - 62 + i * 104
        cv.fill_rect(fx, y + 40, 4, h - 54, (90, 80, 60))
        for s in range(3):
            cv.fill_rect(fx + 4, y + 40 + s * 10, 42, 10, stripes[s])
        cv.circle(fx + 25, y + 55, 4, (200, 40, 40))


def draw_blast(cv, x, y, w, h):
    """A controlled blast goes up over the Iowa ammunition plant."""
    cv.vgrad(x, y, w, h, (150, 180, 210), (228, 200, 150))
    # Distant plant: silos and sheds along the ground line.
    for i in range(4):
        sx = x + 20 + i * 56
        cv.fill_rect(sx, y + h - 54, 42, 26, (120, 118, 112))
        cv.circle(sx + 21, y + h - 54, 21, (140, 138, 130))
    cv.fill_rect(x + 244, y + h - 44, 84, 16, (100, 98, 92))
    cv.triangle(x + 244, y + h - 44, x + 328, y + h - 44, x + 286,
                y + h - 66, (80, 78, 72))
    # Fence line.
    cv.hline(x, y + h - 28, w, (90, 88, 82))
    for i in range(0, w, 48):
        cv.vline(x + i, y + h - 40, 12, (90, 88, 82))
    # Explosion: layered starburst, centre right, kept inside the scene.
    ex, ey = x + int(w * 0.64), y + int(h * 0.46)
    for colour, rad in (((200, 60, 20), 54),
                        ((240, 120, 30), 43),
                        ((250, 190, 50), 32)):
        for k in range(12):
            a0 = k * 30.0 * math.pi / 180.0
            a1 = (k * 30.0 + 14.0) * math.pi / 180.0
            a2 = (k * 30.0 + 30.0) * math.pi / 180.0
            cv.triangle(ex, ey,
                        ex + int(rad * _cos(a0)),
                        ey + int(rad * _sin(a0)),
                        ex + int(rad * 0.45 * _cos(a1)),
                        ey + int(rad * 0.45 * _sin(a1)), colour)
            cv.triangle(ex, ey,
                        ex + int(rad * 0.45 * _cos(a1)),
                        ey + int(rad * 0.45 * _sin(a1)),
                        ex + int(rad * _cos(a2)),
                        ey + int(rad * _sin(a2)), colour)
    cv.circle(ex, ey, 19, (255, 240, 180))
    cv.circle(ex, ey, 11, (255, 255, 230))
    # Smoke puffs drifting up, kept inside the scene.
    for i in range(9):
        sx = ex - 70 + int(hash01(i, 53) * 140)
        sy = ey - 16 - int(hash01(i, 59) * 14)
        cv.circle(sx, sy, 8 + int(hash01(i, 61) * 7), (105, 100, 95))
    # Debris dots.
    for i in range(18):
        dx = ex + int((hash01(i, 67) - 0.5) * 240)
        dy = ey + int((hash01(i, 73) - 0.5) * 90)
        cv.set_px(dx, dy, (60, 55, 50))
        cv.set_px(dx + 1, dy, (60, 55, 50))
    # Big "4 TONNES" tag, left of the blast.
    cv.stamp(x + 14, y + 10, 172, 44, 3, (20, 20, 20))
    cv.text(x + 26, y + 20, "4 TONNES", 3, (20, 20, 20))


# ------------------------------------------------------------ compose --
def draw_masthead(cv):
    cv.fill_rect(16, 16, 992, 124, PAPER)
    cv.text_centred(512, 26, "THE DAILY GLOBE", 6, INK)
    cv.hline(16, 104, 992, INK)
    cv.hline(16, 108, 992, INK)
    cv.text(16, 118, "WEDNESDAY, 25 NOVEMBER 2026", 2, INK)
    right = "FIVE STORIES - ONE DAY"
    cv.text(1008 - text_width(right, 2), 118, right, 2, INK)


def draw_footer(cv):
    line = "SHENZHOU-24 - PACIFIC TREATY - CIA HACK - PUTIN-BRUNEI - IOWA BLAST"
    cv.text_centred(512, 986, line, 1, (90, 84, 70))


def compose():
    cv = Canvas(W, H, PAPER)
    # Paper edge and frame.
    cv.stamp(8, 8, 1008, 1008, 2, INK)
    draw_masthead(cv)

    # Hero: the launch, full width.
    draw_rocket(cv, 16, 148, 992, 322)
    caption(cv, 16, 470, 992, 90,
            "CHINA LAUNCHES SHENZHOU-24",
            "FIRST FOREIGN ASTRONAUT, FROM PAKISTAN, FLIES TO THE TIANGONG "
            "STATION - LIFTOFF FROM JIUQUAN AT 08.18",
            head_scale=3, sub_scale=2)

    # Middle row: the Pacific treaty and the CIA breach.
    draw_treaty(cv, 16, 572, 488, 128)
    caption(cv, 16, 700, 488, 88,
            "PACIFIC PACT IN CANBERRA",
            "AUSTRALIA SIGNS A TREATY WITH SOLOMON ISLANDS - HONIARA "
            "DROPS ITS CHINA SECURITY DEAL",
            head_scale=2, sub_scale=1)
    draw_cyber(cv, 520, 572, 488, 128)
    caption(cv, 520, 700, 488, 88,
            "SPIES HACKED",
            "CIA AND THE DIRECTOR OF NATIONAL INTELLIGENCE HIT BY A "
            "BREACH OF UNCLASSIFIED SYSTEMS",
            head_scale=2, sub_scale=1)

    # Bottom row: the Moscow summit and the Iowa blast.
    draw_summit(cv, 16, 800, 488, 100)
    caption(cv, 16, 900, 488, 72,
            "MOSCOW SUMMIT",
            "PUTIN MEETS THE SULTAN OF BRUNEI ON A STATE VISIT - TALKS "
            "AND A JOINT DECLARATION",
            head_scale=2, sub_scale=1)
    draw_blast(cv, 520, 800, 488, 100)
    caption(cv, 520, 900, 488, 72,
            "4 TONNES UP IN SMOKE",
            "US ARMY DETONATES UNSTABLE EXPLOSIVE AT ITS IOWA AMMUNITION "
            "PLANT IN A CONTROLLED BLAST",
            head_scale=2, sub_scale=1)

    draw_footer(cv)
    return cv


# --------------------------------------------------------------- main --
def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    # Clear only the contents of the output directory, never the
    # directory itself (the grader's parent directory is not writable).
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        try:
            os.chmod(path, 0o644)
        except OSError:
            pass
        if os.path.isfile(path):
            os.remove(path)
    canvas = compose()
    png = encode_png(canvas)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, %dx%d, sha256 %s)"
          % (target, len(png), W, H, hashlib.sha256(png).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
