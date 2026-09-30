#!/usr/bin/env python3
"""MT2009 PLUS Patcher - builds the branded images of the patcher window.

The window keeps the original N2Play Patcher layout and art (flame frame,
buttons, progress bars, news box, ember animation). This script replaces
only the branded parts:

  resources/bg.png              - the frame stays, the inside is the MT2009
                                  SINGLEPLAYER PLUS artwork (logo top right,
                                  where the original had its hero art), the
                                  "N2" logo is gone
  resources/btn_play*.png       - "PLAY" -> "GRAJ"
  resources/btn_vote*.png       - "V4B" -> a coffee cup ("Postaw kawę")
  resources/btn_vps*.png        - new 21x21 button (server icon) in the style
                                  of the minimize/close buttons
  resources/icon.ico            - window/exe icon from our logo

Inputs: tools/oryginal/*.png (the original art), the wiki background
(wiki-src/plus/assets/mt2009plus-tlo.webp) and tools/Cinzel.ttf (OFL).
Needs Pillow:  python3 -m pip install pillow
Run:           python3 tools/grafika.py [--tlo <webp>]
"""
import argparse
import os

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, 'oryginal')
OUT = os.path.join(HERE, '..', 'MT2009-Patcher', 'resources')
DEFAULT_TLO = '/opt/metin2/wiki-src/plus/assets/mt2009plus-tlo.webp'

# Inside of the flame frame of bg.png (window coordinates).
IN_L, IN_T, IN_R, IN_B = 59, 59, 965, 587
# Logo of the artwork (source pixels of mt2009plus-tlo.webp, 1672x941).
LOGO_BOX = (486, 196, 1176, 596)


def orig(name):
    return Image.open(os.path.join(ORIG, name)).convert('RGBA')


def lum(img):
    return img.convert('L')


def linear_mask(size, x0, x1, horizontal=True):
    """0 before x0, 255 after x1, linear between (a cross-fade ramp)."""
    w, h = size
    ramp = Image.new('L', (w if horizontal else h, 1))
    for i in range(ramp.width):
        v = 0 if i <= x0 else 255 if i >= x1 else int(255 * (i - x0) / (x1 - x0))
        ramp.putpixel((i, 0), v)
    if horizontal:
        return ramp.resize((w, h))
    return ramp.resize((h, w)).transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def build_bg(tlo_path):
    bg = orig('bg.png')
    art = Image.open(tlo_path).convert('RGBA')
    W, H = bg.size
    iw, ih = IN_R - IN_L, IN_B - IN_T

    # --- top band: the artwork with its logo on the right (where the
    # original had its heroes), the left part (under the news box) a dark,
    # blurred glow of the same picture.
    s = 0.56
    big = art.resize((round(art.width * s), round(art.height * s)), Image.Resampling.LANCZOS)
    logo_cx = (LOGO_BOX[0] + LOGO_BOX[2]) / 2 * s
    logo_cy = (LOGO_BOX[1] + LOGO_BOX[3]) / 2 * s
    ox = round(772 - logo_cx)
    oy = round(206 - logo_cy)
    content = Image.new('RGBA', (W, H), (20, 6, 5, 255))
    glow = art.resize((iw, round(iw * art.height / art.width)), Image.Resampling.LANCZOS)
    glow = glow.transpose(Image.Transpose.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(18))
    glow = ImageEnhance.Brightness(glow).enhance(0.42)
    content.alpha_composite(glow, (IN_L, IN_T - 40))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.alpha_composite(big, (ox, oy))
    fade = linear_mask((W, H), ox + 110, ox + 290)
    content = Image.composite(layer, content, ImageChops.multiply(fade, layer.getchannel('A')))

    # --- bottom band (below the golden divider): the lower part of the art,
    # blurred and dark, so the progress bars and texts stay readable.
    div_y = 372
    low = art.crop((0, 520, art.width, art.height))
    low = low.resize((iw, round(iw * low.height / low.width)), Image.Resampling.LANCZOS)
    low = low.filter(ImageFilter.GaussianBlur(3))
    low = ImageEnhance.Brightness(low).enhance(0.30)
    low = ImageEnhance.Color(low).enhance(0.7)
    low = Image.blend(low, Image.new('RGBA', low.size, (60, 12, 8, 255)), 0.25)
    bottom = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bottom.alpha_composite(low, (IN_L, IN_B - low.height))
    vfade = linear_mask((W, H), div_y - 6, div_y + 4, horizontal=False)
    content = Image.composite(bottom, content, ImageChops.multiply(vfade, bottom.getchannel('A')))
    # a soft dark vignette over the whole inside
    vign = Image.new('L', (W, H), 0)
    ImageDraw.Draw(vign).rectangle((IN_L + 30, IN_T + 25, IN_R - 30, IN_B - 25), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(28))
    dark = Image.new('RGBA', (W, H), (12, 3, 2, 255))
    content = Image.composite(content, Image.blend(dark, content, 0.45), vign)

    # --- put the new inside into the frame. Near the frame the original
    # flames reach inwards: keep the bright original pixels there.
    result = bg.copy()
    inner = Image.new('L', (W, H), 0)
    ImageDraw.Draw(inner).rectangle((IN_L, IN_T, IN_R - 1, IN_B - 1), fill=255)
    edge = Image.new('L', (W, H), 0)
    ImageDraw.Draw(edge).rectangle((IN_L + 26, IN_T + 22, IN_R - 27, IN_B - 30), fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(9))            # 255 deep inside, 0 at the frame
    flame = lum(bg).point(lambda v: 0 if v < 95 else 255 if v > 175 else int((v - 95) * 255 / 80))
    keep_orig = ImageChops.multiply(flame, ImageChops.invert(edge))
    take_new = ImageChops.multiply(inner, ImageChops.invert(keep_orig))
    result = Image.composite(content, result, take_new)

    # --- the golden divider of the original, copied over the new art. The
    # line is slightly slanted: find its brightest row in the clean middle
    # part, fit a straight line and copy +-3 rows around it.
    src = bg.load()
    dst = result.load()
    xs, ys = [], []
    for x in range(120, 820, 4):
        best, best_y = -1, None
        for y in range(362, 388):
            r, g, b, a = src[x, y]
            score = g + r // 2 - b
            if score > best:
                best, best_y = score, y
        xs.append(x)
        ys.append(best_y)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    # The right end of the original line is covered by its art, so the line
    # is redrawn along the whole width: an averaged vertical profile of the
    # clean stretch (x 150..650), drawn along the fitted line with
    # sub-pixel smoothing.
    prof = [[0.0, 0.0, 0.0, 0.0] for _ in range(9)]
    cnt = 0
    for sx in range(150, 650):
        best, best_y = -1, None
        for y in range(362, 388):
            r, g, b, a = src[sx, y]
            score = g + r // 2 - b
            if score > best:
                best, best_y = score, y
        for i, dy in enumerate(range(-4, 5)):
            r, g, b, a = src[sx, best_y + dy]
            k = min(max((g - 60) / 70, 0), 1) * (1 if r > 110 else 0)
            prof[i][0] += r * k
            prof[i][1] += g * k
            prof[i][2] += b * k
            prof[i][3] += k
        cnt += 1
    rows = []
    for r, g, b, k in prof:
        rows.append(((r / k, g / k, b / k) if k else (0, 0, 0), k / cnt))
    for x in range(IN_L, IN_R):
        cy = my + slope * (x - mx)
        base = int(cy)
        frac = cy - base
        for i, dy in enumerate(range(-4, 5)):
            (cr, cg, cb), k = rows[i]
            if k <= 0.02:
                continue
            for yy, w in ((base + dy, 1 - frac), (base + dy + 1, frac)):
                kk = k * w
                o = dst[x, yy]
                dst[x, yy] = (round(o[0] * (1 - kk) + cr * kk), round(o[1] * (1 - kk) + cg * kk),
                              round(o[2] * (1 - kk) + cb * kk), 255)
    result.save(os.path.join(OUT, 'bg.png'), optimize=True)
    return art


def erase_text(img, box, darker=True, threshold=38):
    """Removes text inside box: every pixel that differs from the smooth
    background (interpolated from the rows above and below the box) is
    replaced with that background."""
    x0, y0, x1, y1 = box
    px = img.load()
    out = img.copy()
    po = out.load()
    for x in range(x0, x1):
        top = [px[x, y0 - k] for k in (1, 2)]
        bot = [px[x, y1 + k] for k in (0, 1)]
        t = tuple(sum(c[i] for c in top) / 2 for i in range(4))
        b = tuple(sum(c[i] for c in bot) / 2 for i in range(4))
        for y in range(y0, y1):
            f = (y - y0 + 1) / (y1 - y0 + 1)
            est = tuple(round(t[i] * (1 - f) + b[i] * f) for i in range(4))
            cur = px[x, y]
            diff = sum(abs(cur[i] - est[i]) for i in range(3))
            if diff > threshold:
                po[x, y] = est
            else:
                # keep the texture but pull it towards the estimate
                po[x, y] = tuple(round((cur[i] + est[i]) / 2) for i in range(4))
    return out


def build_play():
    font = ImageFont.truetype(os.path.join(HERE, 'Cinzel.ttf'), 17)
    try:
        font.set_variation_by_name('Bold')
    except Exception:
        pass
    for name in ('btn_play', 'btn_play_hover', 'btn_play_disable'):
        img = orig(name + '.png')
        img = erase_text(img, (84, 18, 136, 35))
        color = (99, 35, 23, 255)
        if name == 'btn_play_disable':
            color = (110, 55, 35, 255)
        d = ImageDraw.Draw(img)
        text = 'GRAJ'
        l, t, r, b = d.textbbox((0, 0), text, font=font)
        cx, cy = 110, 26.5
        d.text((cx - (l + r) / 2, cy - (t + b) / 2), text, font=font, fill=color)
        img.save(os.path.join(OUT, name + '.png'), optimize=True)


def coffee_glyph(size, scale=8):
    """Cream coffee cup with a dark drop shadow, like the home/discord icons."""
    w, h = size
    S = scale
    g = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    cream = (250, 243, 234, 255)
    # steam
    for sx in (21, 27, 33):
        d.arc((sx * S - 2 * S, 12 * S, sx * S + 2 * S, 16 * S), 90, 270, fill=cream, width=int(1.4 * S))
        d.arc((sx * S - 2 * S, 16 * S, sx * S + 2 * S, 20 * S), 270, 90, fill=cream, width=int(1.4 * S))
    # cup
    d.rounded_rectangle((16 * S, 22 * S, 36 * S, 36 * S), radius=4 * S, fill=cream)
    d.rectangle((16 * S, 22 * S, 36 * S, 27 * S), fill=cream)
    # handle
    d.ellipse((32 * S, 24 * S, 42 * S, 33 * S), outline=cream, width=int(2.4 * S))
    # saucer
    d.rounded_rectangle((12 * S, 37 * S, 40 * S, 40 * S), radius=int(1.5 * S), fill=cream)
    g = g.resize((w, h), Image.Resampling.LANCZOS)
    shadow = Image.new('RGBA', (w, h), (58, 24, 8, 0))
    shadow.putalpha(g.getchannel('A').point(lambda v: int(v * 0.75)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(0.7))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(shadow, (1, 2))
    out.alpha_composite(g)
    return out


def build_vote():
    for name in ('btn_vote', 'btn_vote_hover'):
        img = orig(name + '.png')
        img = erase_text(img, (8, 19, 49, 40), threshold=30)
        img.alpha_composite(coffee_glyph(img.size), (0, 0))
        img.save(os.path.join(OUT, name + '.png'), optimize=True)


def server_glyph(size=21, scale=8):
    S = scale
    g = Image.new('RGBA', (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for top in (5.0, 11.0):
        d.rounded_rectangle((5 * S, top * S, 16 * S, (top + 4.6) * S), radius=int(1.2 * S), fill=(255, 255, 255, 255))
    g = g.resize((size, size), Image.Resampling.LANCZOS)
    return g


def build_vps():
    glyph = server_glyph()
    for src, name in (('btn_minimize', 'btn_vps'), ('btn_minimize_hover', 'btn_vps_hover')):
        img = orig(src + '.png')
        px = img.load()
        # remove the minimize bar: rows 7..12 from the rows around them
        for x in range(2, 19):
            a, b = px[x, 6], px[x, 13]
            for y in range(7, 13):
                f = (y - 6) / 7
                px[x, y] = tuple(round(a[i] * (1 - f) + b[i] * f) for i in range(4))
        # gold gradient like the gear / bar (light top, orange bottom)
        gold = Image.new('RGBA', img.size)
        gp = gold.load()
        light = (245, 214, 68) if name == 'btn_vps' else (252, 232, 96)
        deep = (214, 128, 30) if name == 'btn_vps' else (232, 150, 40)
        for y in range(21):
            f = min(max((y - 4) / 12, 0), 1)
            c = tuple(round(light[i] * (1 - f) + deep[i] * f) for i in range(3))
            for x in range(21):
                gp[x, y] = c + (255,)
        gold.putalpha(glyph.getchannel('A'))
        # the two "LEDs" of the server: dark dots
        shadow = Image.new('RGBA', img.size, (40, 10, 4, 0))
        shadow.putalpha(glyph.getchannel('A').point(lambda v: int(v * 0.6)))
        img.alpha_composite(shadow, (1, 1))
        img.alpha_composite(gold)
        d = ImageDraw.Draw(img)
        for top in (7, 13):
            d.point((13, top), fill=(99, 35, 23, 255))
            d.point((14, top), fill=(99, 35, 23, 255))
        img.save(os.path.join(OUT, name + '.png'), optimize=True)


def build_icon(art):
    cx = (LOGO_BOX[0] + LOGO_BOX[2]) // 2
    cy = (LOGO_BOX[1] + LOGO_BOX[3]) // 2
    side = 720
    crop = art.crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2))
    # darken the corners so the logo stands out
    mask = Image.new('L', crop.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 60, side, side - 60), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    dark = ImageEnhance.Brightness(crop).enhance(0.35)
    crop = Image.composite(crop, dark, mask)
    rounded = Image.new('L', crop.size, 0)
    ImageDraw.Draw(rounded).rounded_rectangle((0, 0, side - 1, side - 1), radius=86, fill=255)
    crop.putalpha(rounded)
    icon = crop.resize((256, 256), Image.Resampling.LANCZOS)
    icon.save(os.path.join(OUT, 'icon.ico'),
              sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (256, 256)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--tlo', default=DEFAULT_TLO, help='grafika tła (mt2009plus-tlo.webp)')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    art = build_bg(args.tlo)
    build_play()
    build_vote()
    build_vps()
    build_icon(art)
    print('Zapisano grafiki w', os.path.normpath(OUT))


if __name__ == '__main__':
    main()
