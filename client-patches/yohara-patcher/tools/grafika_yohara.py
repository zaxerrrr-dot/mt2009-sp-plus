#!/usr/bin/env python3
"""MT2009 PLUS - Yohara Patcher: the window art, made from the 2.x patcher's art.

The Yohara patcher must not look like the 2.x one at a glance (owner, 10 Nov
2026), so at build time (build.sh) this script writes every image of the
window to MT2009-Yohara-Patcher/gen/resources/ (not in git):

  - the flame frame of bg.png, the ember animation (animate/*.png), the GRAJ
    button, the progress bar, the news box, the arrows and the window buttons
    get a turquoise "Yohara" hue instead of the 2.x red/orange fire;
  - bg.png gets a big "YOHARA" under the MT2009 logo;
  - icon.ico: the same hue + a "Y" badge;
  - the artwork inside the frame stays as it is.

Inputs: ../patcher/MT2009-Patcher/resources (the 2.x art) and
../patcher/tools/Cinzel.ttf (OFL). Pillow; deterministic output.
Run:  python3 tools/grafika_yohara.py [--zrodlo DIR] [--wyjscie DIR]
"""
import argparse
import os
import shutil

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PATCHER = os.path.normpath(os.path.join(HERE, '..', '..', 'patcher'))
SRC = os.path.join(PATCHER, 'MT2009-Patcher', 'resources')
FONT = os.path.join(PATCHER, 'tools', 'Cinzel.ttf')
OUT = os.path.normpath(os.path.join(HERE, '..', 'MT2009-Yohara-Patcher', 'gen', 'resources'))

# hue rotation (0..255 = 0..360 deg): red/orange fire -> turquoise
SHIFT = 118
# inside of the flame frame of bg.png (the artwork stays)
IN_L, IN_T, IN_R, IN_B = 66, 70, 958, 576
ACCENT = (94, 230, 214)

UNCHANGED = {'btn_vote.png', 'btn_vote_hover.png', 'dot.png'}
# more contrast for the dark "GRAJ" lettering on the (now bright turquoise) button
CONTRAST = {'btn_play.png', 'btn_play_hover.png', 'btn_play_disable.png'}


def hue(img, shift=SHIFT):
    img = img.convert('RGBA')
    alpha = img.getchannel('A')
    h, s, v = img.convert('RGB').convert('HSV').split()
    h = h.point(lambda x: (x + shift) % 256)
    out = Image.merge('HSV', (h, s, v)).convert('RGB')
    out.putalpha(alpha)
    return out


def contrast(img, k=1.45, mid=150):
    img = img.convert('RGBA')
    alpha = img.getchannel('A')
    h, s, v = img.convert('RGB').convert('HSV').split()
    v = v.point(lambda x: max(0, min(255, int((x - mid) * k + mid))))
    out = Image.merge('HSV', (h, s, v)).convert('RGB')
    out.putalpha(alpha)
    return out


def font(size):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name('Black')
    except Exception:
        try:
            f.set_variation_by_name('Bold')
        except Exception:
            pass
    return f


def text_glow(base, xy, text, size, anchor='mm', spacing=10):
    """Turquoise text with a dark outline and a soft glow, letter-spaced."""
    f = font(size)
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x0 = xy[0] - total / 2 if anchor == 'mm' else xy[0]
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    glow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    g = ImageDraw.Draw(glow)
    x = x0
    for ch, w in zip(text, widths):
        g.text((x, xy[1]), ch, font=f, fill=ACCENT + (200,), anchor='lm')
        d.text((x, xy[1]), ch, font=f, fill=(224, 255, 250, 255), anchor='lm',
               stroke_width=3, stroke_fill=(6, 30, 34, 255))
        x += w + spacing
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    base.alpha_composite(glow)
    base.alpha_composite(glow)
    base.alpha_composite(layer)
    # thin turquoise fill over the light core (keeps it readable on the art)
    core = Image.new('RGBA', base.size, (0, 0, 0, 0))
    c = ImageDraw.Draw(core)
    x = x0
    for ch, w in zip(text, widths):
        c.text((x, xy[1]), ch, font=f, fill=ACCENT + (150,), anchor='lm')
        x += w + spacing
    base.alpha_composite(core)


def build_bg(src, out):
    bg = Image.open(os.path.join(src, 'bg.png')).convert('RGBA')
    shifted = hue(bg)
    inside = bg.crop((IN_L, IN_T, IN_R, IN_B))
    shifted.paste(inside, (IN_L, IN_T))
    # the thin gold divider line across the artwork -> turquoise as well
    line = bg.crop((IN_L, 366, IN_R, 382))
    shifted.paste(hue(line), (IN_L, 366))
    text_glow(shifted, (775, 322), 'YOHARA', 50)
    shifted.save(os.path.join(out, 'bg.png'), optimize=False)


def build_icon(src, out):
    icon = Image.open(os.path.join(src, 'icon.ico'))
    icon.size = max(icon.ico.sizes())
    big = hue(icon.convert('RGBA')).resize((256, 256), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    d.ellipse((148, 148, 252, 252), fill=(8, 40, 44, 255), outline=ACCENT + (255,), width=8)
    d.text((200, 203), 'Y', font=font(84), fill=ACCENT + (255,), anchor='mm')
    big.save(os.path.join(out, 'icon.ico'),
             sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (256, 256)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--zrodlo', default=SRC)
    ap.add_argument('--wyjscie', default=OUT)
    a = ap.parse_args()
    if os.path.isdir(a.wyjscie):
        shutil.rmtree(a.wyjscie)
    os.makedirs(os.path.join(a.wyjscie, 'animate'))
    n = 0
    for name in sorted(os.listdir(a.zrodlo)):
        path = os.path.join(a.zrodlo, name)
        if name == 'animate':
            for frame in sorted(os.listdir(path)):
                hue(Image.open(os.path.join(path, frame))).save(os.path.join(a.wyjscie, 'animate', frame))
                n += 1
        elif name == 'bg.png':
            build_bg(a.zrodlo, a.wyjscie)
            n += 1
        elif name == 'icon.ico':
            build_icon(a.zrodlo, a.wyjscie)
            n += 1
        elif name.endswith('.png'):
            if name in UNCHANGED:
                shutil.copyfile(path, os.path.join(a.wyjscie, name))
            else:
                img = hue(Image.open(path))
                if name in CONTRAST:
                    img = contrast(img)
                img.save(os.path.join(a.wyjscie, name))
            n += 1
    print('grafika Yohary: %d plików -> %s' % (n, a.wyjscie))


if __name__ == '__main__':
    main()
