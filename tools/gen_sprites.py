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
    pad = B * 0.085
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).rounded_rectangle([pad, pad, B - pad, B - pad],
                                           radius=int(B * 0.34), fill=255)
    img = fill_shaded(mask, base, dark, light)

    # Scale diamonds with a darker lower edge -> reads as overlapping scales.
    sc = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sc)
    for (ox, oy) in [(0, -0.17), (-0.17, 0.10), (0.17, 0.10), (0, 0.34)]:
        cx, cy = B / 2 + ox * B, B / 2 + oy * B
        s = B * 0.10
        sd.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)],
                   fill=light + (120,))
        sd.line([(cx - s, cy), (cx, cy + s)], fill=dark + (110,), width=int(B * 0.012))
        sd.line([(cx, cy + s), (cx + s, cy)], fill=dark + (110,), width=int(B * 0.012))
    scm = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    scm.paste(sc, (0, 0), mask)
    img = Image.alpha_composite(img, scm)

    img = add_gloss(img, mask, [B * 0.2, B * 0.14, B * 0.62, B * 0.46], 95)
    img = outline_behind(img, mask, px=B * 0.045)
    return down(img)


# ----------------------------------------------------------------- snake head
def make_head(base=GREEN, dark=GREEN_D, light=GREEN_L):
    pad = B * 0.09
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).rounded_rectangle([pad, pad, B - pad, B - pad],
                                           radius=int(B * 0.42), fill=255)
    img = fill_shaded(mask, base, dark, light)
    img = add_gloss(img, mask, [B * 0.18, B * 0.12, B * 0.62, B * 0.42], 120)
    img = outline_behind(img, mask, px=B * 0.05)

    d = ImageDraw.Draw(img)
    # Forked tongue flicking out the front (head faces RIGHT at rotation 0).
    ty = B * 0.5
    d.line([(B * 0.82, ty), (B * 0.96, ty)], fill=(228, 56, 78), width=int(B * 0.035))
    d.line([(B * 0.96, ty), (B * 0.995, ty - B * 0.045)], fill=(228, 56, 78), width=int(B * 0.028))
    d.line([(B * 0.96, ty), (B * 0.995, ty + B * 0.045)], fill=(228, 56, 78), width=int(B * 0.028))

    # Eyes: white socket, coloured iris, pupil, catchlight.
    iris = tuple(min(255, int(c * 0.45) + j) for c, j in zip(base, (8, 50, 24)))
    for ey in (B * 0.33, B * 0.67):
        d.ellipse([B * 0.585, ey - B * 0.15, B * 0.87, ey + B * 0.15], fill=WHITE)
        d.ellipse([B * 0.585, ey - B * 0.15, B * 0.87, ey + B * 0.15],
                  outline=dark, width=int(B * 0.012))
        d.ellipse([B * 0.66, ey - B * 0.09, B * 0.81, ey + B * 0.09], fill=iris)
        d.ellipse([B * 0.695, ey - B * 0.058, B * 0.775, ey + B * 0.058], fill=(14, 18, 26))
        d.ellipse([B * 0.705, ey - B * 0.05, B * 0.745, ey - B * 0.012], fill=WHITE)
    return down(img)


# ----------------------------------------------------------------- snake tail
def make_tail(base=GREEN, dark=GREEN_D, light=GREEN_L):
    # Wide rounded end on the RIGHT (connects to body), taper to a point on LEFT.
    mask = Image.new("L", (B, B), 0)
    ImageDraw.Draw(mask).polygon(
        [(B * 0.14, B * 0.5), (B * 0.56, B * 0.2), (B * 0.9, B * 0.2),
         (B * 0.9, B * 0.8), (B * 0.56, B * 0.8)], fill=255)
    ImageDraw.Draw(mask).rounded_rectangle([B * 0.56, B * 0.2, B * 0.91, B * 0.8],
                                           radius=int(B * 0.16), fill=255)
    img = fill_shaded(mask, base, dark, light)
    img = add_gloss(img, mask, [B * 0.5, B * 0.22, B * 0.85, B * 0.46], 95)
    img = outline_behind(img, mask, px=B * 0.045)
    return down(img)


# ----------------------------------------------------------------- fruit
def _fruit_frame(i, base, dark, light, glow_c, sparkle=False):
    img = canvas()
    bob = math.sin(i / 4 * math.tau) * B * 0.02
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

    gx = cx - rw * 0.42 + (i / 4) * rw * 0.4
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

    pulse = 0.6 + 0.4 * math.sin(i / 4 * math.tau)
    cr = rr * (0.24 + 0.07 * pulse)
    img = Image.alpha_composite(img, soft_glow((255, 70, 60),
        [cx - cr * 2.6, cy - cr * 2.6, cx + cr * 2.6, cy + cr * 2.6], B * 0.05, int(170 * pulse)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, int(90 + 90 * pulse), 70))
    d.ellipse([cx - cr * 0.4, cy - cr * 0.5, cx + cr * 0.1, cy], fill=(255, 235, 200))
    img = add_gloss(img, mask, [cx - rr * 0.7, cy - rr * 0.85, cx - rr * 0.05, cy - rr * 0.2], 70)
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


make_body().save(os.path.join(OUT, "body.png"))
make_head().save(os.path.join(OUT, "head.png"))
make_tail().save(os.path.join(OUT, "tail.png"))

P2_BASE, P2_DARK, P2_LIGHT = (240, 150, 70), (150, 80, 28), (255, 214, 156)
make_body(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "body_p2.png"))
make_head(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "head_p2.png"))
make_tail(P2_BASE, P2_DARK, P2_LIGHT).save(os.path.join(OUT, "tail_p2.png"))

save_strip([apple_frame(i) for i in range(4)], "food.png")
save_strip([bonus_frame(i) for i in range(4)], "bonus.png")
save_strip([mine_frame(i) for i in range(4)], "mine.png")

badge(CYAN, icon_slowmo).save(os.path.join(OUT, "pu_slowmo.png"))
badge(PURPLE, icon_double).save(os.path.join(OUT, "pu_double.png"))
badge(ORANGE, icon_magnet).save(os.path.join(OUT, "pu_magnet.png"))
badge(GHOST_C, icon_ghost).save(os.path.join(OUT, "pu_ghost.png"))
print("sprites written to", OUT)
