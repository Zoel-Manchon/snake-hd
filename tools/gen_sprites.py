"""Generate Snake HD sprites with Pillow (v2 - polished).

Drawn at 8x and downsampled with LANCZOS for clean edges. Every solid sprite
gets a dark outline so it reads against busy biome backgrounds, a directional
gloss + ambient-occlusion light model, and crisper detail (iris eyes, a flicking
tongue, a rounder glossy apple, a meaner mine, font-rendered "X2").

Run from the repo root so OUT and the font path resolve:
    cd snake-hd && python /home/claude/gen_sprites.py

Animated sprites (food/bonus/mine) are 4-frame 160x40 strips; the rest are
single 40x40 cells. Palette matches game/settings.py.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 40            # final cell size
SS = 8            # supersample factor
B = S * SS        # 320, working resolution
OUT = "assets/sprites"
os.makedirs(OUT, exist_ok=True)

GREEN   = (95, 208, 104)
GREEN_D = (40, 110, 60)
GREEN_L = (180, 245, 168)
RED     = (224, 64, 72)
RED_D   = (140, 28, 40)
RED_L   = (255, 158, 158)
GOLD    = (255, 198, 70)
GOLD_D  = (190, 130, 26)
GOLD_L  = (255, 244, 180)
STEEL_D = (30, 34, 50)
CYAN    = (86, 180, 225)
PURPLE  = (190, 130, 240)
ORANGE  = (235, 130, 100)
WHITE   = (245, 248, 255)
OUTLINE = (16, 20, 28)        # near-black rim for contrast

try:
    FONT_X2 = ImageFont.truetype("assets/PressStart2P.ttf", int(B * 0.40))
except OSError:
    FONT_X2 = None


def canvas():
    return Image.new("RGBA", (B, B), (0, 0, 0, 0))


def down(img):
    return img.resize((S, S), Image.LANCZOS)


def vgrad(top, bottom):
    g = Image.new("RGBA", (B, B))
    d = ImageDraw.Draw(g)
    for y in range(B):
        t = y / (B - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (B, y)], fill=c)
    return g


def grow(mask, px):
    k = int(px) | 1
    return mask.filter(ImageFilter.MaxFilter(max(3, k)))


def outline_behind(img, mask, color=OUTLINE, px=None):
    """Composite a solid silhouette (mask grown by px) behind img."""
    if px is None:
        px = B * 0.05
    layer = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", (B, B), color + (255,)), (0, 0), grow(mask, px))
    return Image.alpha_composite(layer, img)


def fill_shaded(mask, base, dark, light):
    """Vertical gradient fill + a soft ambient-occlusion shadow at the bottom."""
    out = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    out.paste(vgrad(light, base), (0, 0), mask)
    ao = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    ImageDraw.Draw(ao).ellipse([B * 0.04, B * 0.52, B * 0.96, B * 1.18], fill=dark + (165,))
    ao = ao.filter(ImageFilter.GaussianBlur(B * 0.09))
    aom = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    aom.paste(ao, (0, 0), mask)
    return Image.alpha_composite(out, aom)


def add_gloss(img, mask, box, alpha=130, blur=0.045):
    h = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    ImageDraw.Draw(h).ellipse(box, fill=(255, 255, 255, alpha))
    h = h.filter(ImageFilter.GaussianBlur(B * blur))
    hm = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    hm.paste(h, (0, 0), mask)
    return Image.alpha_composite(img, hm)


def soft_glow(color, box, blur, alpha=160):
    g = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(box, fill=color + (alpha,))
    return g.filter(ImageFilter.GaussianBlur(blur))


def star(d, cx, cy, r, color, alpha=255):
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i
        rad = r if i % 2 == 0 else r * 0.38
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    d.polygon(pts, fill=color + (alpha,))


# ----------------------------------------------------------------- snake body
def make_body(base=GREEN, dark=GREEN_D, light=GREEN_L):
    """Horizontal tube segment: flush on LEFT and RIGHT so segments connect."""
    P = B * 0.11
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).rectangle([0, P, B, B - P], fill=255)
    img = fill_shaded(mask, base, dark, light)

    sc = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sc)
    for ox in (-0.25, 0.0, 0.25):
        cx, cy = B / 2 + ox * B, B / 2
        sz = B * 0.085
        sd.polygon([(cx, cy - sz), (cx + sz, cy), (cx, cy + sz), (cx - sz, cy)],
                   fill=light + (115,))
        sd.line([(cx - sz, cy), (cx, cy + sz)], fill=dark + (105,), width=int(B * 0.012))
        sd.line([(cx, cy + sz), (cx + sz, cy)], fill=dark + (105,), width=int(B * 0.012))
    scm = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    scm.paste(sc, (0, 0), mask)
    img = Image.alpha_composite(img, scm)

    d = ImageDraw.Draw(img)
    d.line([(0, B * 0.24), (B, B * 0.24)], fill=dark + (70,), width=int(B * 0.028))
    d.rectangle([0, B * 0.72, B, B * 0.83], fill=light + (48,))
    img = add_gloss(img, mask, [B * 0.05, B * 0.13, B * 0.95, B * 0.42], 90)
    img = outline_behind(img, mask, px=B * 0.04)
    return down(img)


def make_corner(base=GREEN, dark=GREEN_D, light=GREEN_L):
    """Elbow segment: open on LEFT and DOWN at rotation 0 (rotate for others)."""
    P = B * 0.11
    R = int(B * 0.34)
    mask = Image.new("L", (B, B), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, P, B - P, B - P], radius=R,
                         corners=(False, True, False, False), fill=255)
    md.rounded_rectangle([P, P, B - P, B], radius=R,
                         corners=(False, True, False, False), fill=255)
    img = fill_shaded(mask, base, dark, light)

    sc = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sc)
    cx, cy = B * 0.44, B * 0.56
    sz = B * 0.085
    sd.polygon([(cx, cy - sz), (cx + sz, cy), (cx, cy + sz), (cx - sz, cy)],
               fill=light + (115,))
    scm = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    scm.paste(sc, (0, 0), mask)
    img = Image.alpha_composite(img, scm)

    img = add_gloss(img, mask, [B * 0.06, B * 0.13, B * 0.72, B * 0.4], 85)
    img = outline_behind(img, mask, px=B * 0.04)
    return down(img)


# ----------------------------------------------------------------- snake head
def make_head(base=GREEN, dark=GREEN_D, light=GREEN_L):
    """Sleek capsule head that matches the smooth tube body: rounded snout on
    the RIGHT, softly rounded back, big irised eyes with brows, tiny nostrils."""
    cy = B * 0.5
    mask = Image.new("L", (B, B), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([B * 0.26, cy - B * 0.335, B * 0.94, cy + B * 0.335], fill=255)   # snout dome
    md.rounded_rectangle([B * 0.03, cy - B * 0.295, B * 0.62, cy + B * 0.295],
                         radius=int(B * 0.27), fill=255)                          # rounded back
    img = fill_shaded(mask, base, dark, light)
    img = add_gloss(img, mask, [B * 0.12, B * 0.14, B * 0.66, B * 0.44], 120)
    img = outline_behind(img, mask, px=B * 0.045)

    d = ImageDraw.Draw(img)
    iris = tuple(min(255, int(c * 0.45) + j) for c, j in zip(base, (8, 50, 24)))
    for sy in (-1, 1):
        ey = cy + sy * B * 0.165
        d.ellipse([B * 0.50, ey - B * 0.145, B * 0.80, ey + B * 0.145], fill=WHITE)
        d.ellipse([B * 0.50, ey - B * 0.145, B * 0.80, ey + B * 0.145],
                  outline=dark, width=int(B * 0.012))
        d.ellipse([B * 0.585, ey - B * 0.09, B * 0.735, ey + B * 0.09], fill=iris)
        d.ellipse([B * 0.618, ey - B * 0.055, B * 0.698, ey + B * 0.055], fill=(14, 18, 26))
        d.ellipse([B * 0.628, ey - B * 0.048, B * 0.666, ey - B * 0.012], fill=WHITE)
        d.arc([B * 0.49, ey - B * 0.20 * sy - B * 0.10, B * 0.80, ey - B * 0.20 * sy + B * 0.16],
              200 if sy < 0 else 20, 340 if sy < 0 else 160, fill=dark, width=int(B * 0.02))
    d.ellipse([B * 0.885, cy - B * 0.075, B * 0.915, cy - B * 0.030], fill=dark)
    d.ellipse([B * 0.885, cy + B * 0.030, B * 0.915, cy + B * 0.075], fill=dark)
    return down(img)


# ----------------------------------------------------------------- snake tail
def make_tail(base=GREEN, dark=GREEN_D, light=GREEN_L):
    """Taper to a point on the LEFT; RIGHT side flush to join the body."""
    P = B * 0.11
    mask = Image.new("L", (B, B), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(B * 0.06, B * 0.5), (B * 0.55, P), (B, P), (B, B - P), (B * 0.55, B - P)],
               fill=255)
    img = fill_shaded(mask, base, dark, light)
    img = add_gloss(img, mask, [B * 0.4, B * 0.14, B * 0.98, B * 0.42], 90)
    img = outline_behind(img, mask, px=B * 0.04)
    return down(img)


# ----------------------------------------------------------------- fruit
N_FRAMES = 8      # frames per animation strip (smoother at 8)


def _fruit_frame(i, base, dark, light, glow_c, sparkle=False):
    img = canvas()
    bob = math.sin(i / N_FRAMES * math.tau) * B * 0.02
    cx, cy = B * 0.5, B * 0.57 + bob
    rw, rh = B * 0.31, B * 0.30
    img = Image.alpha_composite(img, soft_glow(glow_c, [cx - rw, cy - rh, cx + rw, cy + rh],
                                               B * 0.06, 90))

    # Round body with a small dimple at the top.
    mask = Image.new("L", (B, B), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=255)
    md.ellipse([cx - rw * 0.22, cy - rh * 1.04, cx + rw * 0.22, cy - rh * 0.62], fill=0)

    body = fill_shaded(mask, base, dark, light)
    body = outline_behind(body, mask, px=B * 0.04)
    img = Image.alpha_composite(img, body)

    d = ImageDraw.Draw(img)
    d.line([(cx, cy - rh * 0.86), (cx + B * 0.02, cy - rh * 1.5)],
           fill=(110, 72, 42), width=int(B * 0.045))
    lf = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lf)
    ld.ellipse([cx + B * 0.02, cy - rh * 1.62, cx + B * 0.22, cy - rh * 1.12],
               fill=(86, 184, 96))
    ld.line([(cx + B * 0.05, cy - rh * 1.5), (cx + B * 0.19, cy - rh * 1.22)],
            fill=(48, 120, 60), width=int(B * 0.012))
    img = Image.alpha_composite(img, lf)

    gx = cx - rw * 0.42 + (i / N_FRAMES) * rw * 0.4
    img = add_gloss(img, mask, [gx - B * 0.1, cy - rh * 0.72, gx + B * 0.06, cy + rh * 0.05],
                    alpha=150, blur=0.035)
    ImageDraw.Draw(img).ellipse([cx - rw * 0.42, cy - rh * 0.5, cx - rw * 0.24, cy - rh * 0.28],
                                fill=(255, 255, 255, 230))

    if sparkle:
        d = ImageDraw.Draw(img)
        spots = [(B * 0.74, B * 0.3), (B * 0.3, B * 0.66), (B * 0.68, B * 0.74)]
        sx, sy = spots[i % len(spots)]
        star(d, sx, sy, B * 0.1, GOLD_L)
        star(d, B - sx, B * 0.22, B * 0.06, WHITE, 220)
    return img


def apple_frame(i):
    return _fruit_frame(i, RED, RED_D, RED_L, RED)


def bonus_frame(i):
    return _fruit_frame(i, GOLD, GOLD_D, GOLD_L, GOLD, sparkle=True)


# ----------------------------------------------------------------- mine
def mine_frame(i):
    img = canvas()
    cx, cy = B * 0.5, B * 0.5
    rr = B * 0.30
    d = ImageDraw.Draw(img)

    for k in range(8):
        a = math.pi / 4 * k
        tipx, tipy = cx + math.cos(a) * rr * 1.42, cy + math.sin(a) * rr * 1.42
        perp = a + math.pi / 2
        bw = rr * 0.22
        b1 = (cx + math.cos(a) * rr * 0.85 + math.cos(perp) * bw,
              cy + math.sin(a) * rr * 0.85 + math.sin(perp) * bw)
        b2 = (cx + math.cos(a) * rr * 0.85 - math.cos(perp) * bw,
              cy + math.sin(a) * rr * 0.85 - math.sin(perp) * bw)
        d.polygon([b1, b2, (tipx, tipy)], fill=STEEL_D)
        d.line([b1, (tipx, tipy)], fill=(120, 128, 156), width=int(B * 0.02))

    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
    body = fill_shaded(mask, (96, 104, 134), STEEL_D, (140, 148, 178))
    body = outline_behind(body, mask, px=B * 0.035)
    img = Image.alpha_composite(img, body)
    d = ImageDraw.Draw(img)
    for k in range(8):
        a = math.pi / 4 * k + math.pi / 8
        rx, ry = cx + math.cos(a) * rr * 0.7, cy + math.sin(a) * rr * 0.7
        d.ellipse([rx - B * 0.018, ry - B * 0.018, rx + B * 0.018, ry + B * 0.018],
                  fill=(150, 158, 188))

    pulse = 0.6 + 0.4 * math.sin(i / N_FRAMES * math.tau)
    cr = rr * (0.24 + 0.07 * pulse)
    img = Image.alpha_composite(img, soft_glow((255, 70, 60),
        [cx - cr * 2.6, cy - cr * 2.6, cx + cr * 2.6, cy + cr * 2.6], B * 0.05, int(170 * pulse)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, int(90 + 90 * pulse), 70))
    d.ellipse([cx - cr * 0.4, cy - cr * 0.5, cx + cr * 0.1, cy], fill=(255, 235, 200))
    img = add_gloss(img, mask, [cx - rr * 0.7, cy - rr * 0.85, cx - rr * 0.05, cy - rr * 0.2], 70)
    return img




# ----------------------------------------------------------------- enemies
def drifter_frame(i):
    """Cyan jelly: glowing dome with swaying tentacles - drifts around the board."""
    img = canvas()
    ph = i / N_FRAMES * math.tau
    cx, cy = B * 0.5, B * 0.46 + math.sin(ph) * B * 0.03
    rw, rh = B * 0.30, B * 0.26
    img = Image.alpha_composite(img, soft_glow(CYAN, [cx - rw * 1.2, cy - rh * 1.2,
                                                      cx + rw * 1.2, cy + rh * 1.2], B * 0.07, 80))
    mask = Image.new("L", (B, B), 0)
    md = ImageDraw.Draw(mask)
    md.pieslice([cx - rw, cy - rh, cx + rw, cy + rh * 1.6], 180, 360, fill=255)
    md.rectangle([cx - rw, cy, cx + rw, cy + rh * 0.28], fill=255)
    body = fill_shaded(mask, (70, 170, 210), (30, 90, 130), (150, 230, 250))
    body = outline_behind(body, mask, px=B * 0.035)
    img = Image.alpha_composite(img, body)
    d = ImageDraw.Draw(img)
    for k, tx in enumerate((-0.55, -0.18, 0.18, 0.55)):
        sway = math.sin(ph + k * 1.4) * B * 0.045
        x0 = cx + tx * rw
        d.line([(x0, cy + rh * 0.24), (x0 + sway, cy + rh * 1.05)],
               fill=(120, 210, 235), width=int(B * 0.035))
    d.ellipse([cx - rw * 0.45, cy - rh * 0.55, cx - rw * 0.05, cy - rh * 0.1],
              fill=(235, 250, 255, 200))
    inner = math.sin(ph) * rw * 0.18
    d.ellipse([cx - B * 0.05 + inner, cy - B * 0.02, cx + B * 0.05 + inner, cy + B * 0.07],
              fill=(190, 240, 255, 160))
    return img


def blinker_frame(i):
    """Amber phase crystal: a diamond that pulses bright as it turns solid."""
    img = canvas()
    ph = i / N_FRAMES * math.tau
    pulse = 0.5 + 0.5 * math.sin(ph)
    cx, cy = B * 0.5, B * 0.5
    r = B * 0.30 + pulse * B * 0.02
    img = Image.alpha_composite(img, soft_glow((250, 150, 80),
        [cx - r * 1.3, cy - r * 1.3, cx + r * 1.3, cy + r * 1.3], B * 0.06, int(60 + 120 * pulse)))
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).polygon([(cx, cy - r), (cx + r * 0.72, cy), (cx, cy + r), (cx - r * 0.72, cy)], fill=255)
    body = fill_shaded(mask, (235, 130, 70), (150, 60, 30), (255, 210, 150))
    body = outline_behind(body, mask, px=B * 0.035)
    img = Image.alpha_composite(img, body)
    d = ImageDraw.Draw(img)
    ir = r * (0.42 + 0.16 * pulse)
    d.polygon([(cx, cy - ir), (cx + ir * 0.72, cy), (cx, cy + ir), (cx - ir * 0.72, cy)],
              fill=(255, int(200 + 55 * pulse), 170, int(150 + 100 * pulse)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 240, 220, 90), width=int(B * 0.012))
    oa = ph
    ox, oy = cx + math.cos(oa) * r * 1.05, cy + math.sin(oa) * r * 1.05
    star(d, ox, oy, B * 0.045, (255, 230, 180), 220)
    return img


def chaser_frame(i):
    """Red seeker: an angry hunter orb with a slit pupil and thruster fins."""
    img = canvas()
    ph = i / N_FRAMES * math.tau
    pulse = 0.5 + 0.5 * math.sin(ph * 2)
    cx, cy = B * 0.5, B * 0.5
    r = B * 0.28
    img = Image.alpha_composite(img, soft_glow((255, 70, 70),
        [cx - r * 1.45, cy - r * 1.45, cx + r * 1.45, cy + r * 1.45], B * 0.06, int(90 + 90 * pulse)))
    d = ImageDraw.Draw(img)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4 + math.sin(ph) * 0.12
        x1, y1 = cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9
        x2, y2 = cx + math.cos(a) * r * 1.38, cy + math.sin(a) * r * 1.38
        perp = a + math.pi / 2
        w = r * 0.2
        d.polygon([(x1 + math.cos(perp) * w, y1 + math.sin(perp) * w),
                   (x1 - math.cos(perp) * w, y1 - math.sin(perp) * w), (x2, y2)],
                  fill=(150, 30, 40))
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    body = fill_shaded(mask, (215, 55, 65), (120, 20, 32), (255, 140, 130))
    body = outline_behind(body, mask, px=B * 0.035)
    img = Image.alpha_composite(img, body)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r * 0.55, cy - r * 0.5, cx + r * 0.55, cy + r * 0.5], fill=(255, 235, 210))
    pw = r * (0.14 + 0.05 * pulse)
    d.ellipse([cx - pw, cy - r * 0.36, cx + pw, cy + r * 0.36], fill=(20, 10, 14))
    d.ellipse([cx - pw * 0.4, cy - r * 0.28, cx + pw * 0.15, cy - r * 0.1], fill=WHITE)
    for sx in (-1, 1):
        d.line([(cx + sx * r * 0.62, cy - r * 0.62), (cx + sx * r * 0.12, cy - r * 0.3)],
               fill=(90, 12, 22), width=int(B * 0.05))
    return img


# ----------------------------------------------------------------- power-ups
def badge(color, draw_icon):
    img = canvas()
    pad = B * 0.10
    box = [pad, pad, B - pad, B - pad]
    img = Image.alpha_composite(img, soft_glow(color, box, B * 0.05, 110))
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=int(B * 0.30), fill=255)

    body = fill_shaded(mask, color, tuple(int(c * 0.5) for c in color),
                       tuple(min(255, int(c * 1.3)) for c in color))
    body = outline_behind(body, mask, px=B * 0.04)
    img = Image.alpha_composite(img, body)
    img = add_gloss(img, mask, [B * 0.18, B * 0.14, B * 0.62, B * 0.44], 80)

    vg = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    ImageDraw.Draw(vg).ellipse([B * 0.28, B * 0.3, B * 0.72, B * 0.74], fill=(0, 0, 0, 55))
    vg = vg.filter(ImageFilter.GaussianBlur(B * 0.06))
    vgm = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    vgm.paste(vg, (0, 0), mask)
    img = Image.alpha_composite(img, vgm)

    draw_icon(ImageDraw.Draw(img))
    return down(img)


def icon_slowmo(d):
    cx, cy, r = B * 0.5, B * 0.53, B * 0.22
    w = int(B * 0.055)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=w)
    d.line([(cx, cy), (cx, cy - r * 0.62)], fill=WHITE, width=w)
    d.line([(cx, cy), (cx + r * 0.52, cy + r * 0.16)], fill=WHITE, width=w)
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        x1, y1 = cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78
        x2, y2 = cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92
        d.line([(x1, y1), (x2, y2)], fill=WHITE, width=int(B * 0.02))
    d.ellipse([cx - B * 0.035, cy - r - B * 0.07, cx + B * 0.035, cy - r + B * 0.02], fill=WHITE)


def icon_double(d):
    if FONT_X2:
        d.text((B * 0.51, B * 0.55), "X2", font=FONT_X2, fill=(0, 0, 0, 130), anchor="mm")
        d.text((B * 0.5, B * 0.53), "X2", font=FONT_X2, fill=WHITE, anchor="mm")
    else:
        d.text((B * 0.3, B * 0.4), "X2", fill=WHITE)


def icon_magnet(d):
    cx, cy = B * 0.5, B * 0.44
    rO, rI = B * 0.24, B * 0.12
    d.arc([cx - rO, cy - rO, cx + rO, cy + rO], 180, 360, fill=WHITE, width=int(rO - rI))
    for sx in (-1, 1):
        x = cx + sx * (rO + rI) / 2
        d.rectangle([x - (rO - rI) / 2, cy, x + (rO - rI) / 2, cy + B * 0.2], fill=WHITE)
        d.rectangle([x - (rO - rI) / 2, cy + B * 0.17, x + (rO - rI) / 2, cy + B * 0.25],
                    fill=(220, 70, 70) if sx < 0 else (70, 120, 220))


GHOST_C = (90, 200, 255)


def icon_ghost(d):
    cx = B * 0.5
    top, bot, half = B * 0.34, B * 0.62, B * 0.18
    d.pieslice([cx - half, top - half, cx + half, top + half], 180, 360, fill=WHITE)
    d.rectangle([cx - half, top, cx + half, bot], fill=WHITE)
    r = half / 3.0
    for i in range(3):
        bx = cx - half + r * (2 * i + 1)
        d.ellipse([bx - r, bot - r, bx + r, bot + r], fill=WHITE)
    er = half * 0.3
    for sx in (-1, 1):
        ex, ey = cx + sx * half * 0.42, top + half * 0.1
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(36, 66, 92))


# ----------------------------------------------------------------- write files
def save_strip(frames, name):
    strip = Image.new("RGBA", (S * len(frames), S), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(down(fr), (i * S, 0))
    strip.save(os.path.join(OUT, name))


SKINS = {
    "":       ((95, 208, 104), (40, 110, 60), (180, 245, 168)),
    "_red":   ((214, 62, 74), (122, 22, 38), (255, 152, 142)),
    "_black": ((60, 64, 82), (20, 22, 32), (148, 154, 186)),
    "_blue":  ((72, 152, 235), (26, 72, 142), (162, 216, 255)),
    "_gold":  ((252, 190, 66), (172, 112, 22), (255, 242, 176)),
}
for suf, (b_, d_, l_) in SKINS.items():
    make_body(b_, d_, l_).save(os.path.join(OUT, f"body{suf}.png"))
    make_head(b_, d_, l_).save(os.path.join(OUT, f"head{suf}.png"))
    make_tail(b_, d_, l_).save(os.path.join(OUT, f"tail{suf}.png"))
    make_corner(b_, d_, l_).save(os.path.join(OUT, f"corner{suf}.png"))

P2_BASE, P2_DARK, P2_LIGHT = (240, 150, 70), (150, 80, 28), (255, 214, 156)
make_body(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "body_p2.png"))
make_head(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "head_p2.png"))
make_tail(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "tail_p2.png"))
make_corner(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "corner_p2.png"))

save_strip([apple_frame(i) for i in range(N_FRAMES)], "food.png")
save_strip([bonus_frame(i) for i in range(N_FRAMES)], "bonus.png")
save_strip([mine_frame(i) for i in range(N_FRAMES)], "mine.png")
save_strip([drifter_frame(i) for i in range(N_FRAMES)], "drifter.png")
save_strip([blinker_frame(i) for i in range(N_FRAMES)], "blinker.png")
save_strip([chaser_frame(i) for i in range(N_FRAMES)], "chaser.png")

badge(CYAN, icon_slowmo).save(os.path.join(OUT, "pu_slowmo.png"))
badge(PURPLE, icon_double).save(os.path.join(OUT, "pu_double.png"))
badge(ORANGE, icon_magnet).save(os.path.join(OUT, "pu_magnet.png"))
badge(GHOST_C, icon_ghost).save(os.path.join(OUT, "pu_ghost.png"))
print("sprites written to", OUT)
