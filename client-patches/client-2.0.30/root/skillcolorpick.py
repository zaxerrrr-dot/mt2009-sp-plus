# MT2009_PLUS_SKILL_COLOR_V1: Kolor umiejetnosci - the colour picker's arithmetic, without a single client module, so
# the client build's tool (client-2.0.30/tools/skillcolor) paints d:/ymir work/ui/skillcolor/color_picker.tga from the
# very same function the window (uiskillcolor.py) reads a click with: the colour under the mouse is computed, not
# read off the screen (the package's wndMgr.GetColorAtPosition took a screenshot pixel - wrong under any scaling).
# Python 2 (the client) and 3 (the tool).

PICKER_WIDTH = 180
PICKER_HEIGHT = 120

# the darkest colour the window takes (0-255, the strongest of r/g/b): the exe multiplies a particle's brightness by
# the colour, so a black one would make the skill's effect invisible
MIN_BRIGHTNESS = 40

# the colour bars' "no colour" (the effect's own) - shown as this grey
DEFAULT_SHOWN = (90, 90, 90)


def _hsv(h, s, v):
	# h, s, v in 0..1 -> r, g, b 0..255 (colorsys is not in the client's python)
	h = (h % 1.0) * 6.0
	i = int(h)
	f = h - i
	p = v * (1.0 - s)
	q = v * (1.0 - s * f)
	t = v * (1.0 - s * (1.0 - f))
	r, g, b = ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))[i % 6]
	return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def ColorAt(x, y):
	"""The picker's colour at its pixel (x, y): the hue left to right; the upper half from white to the full colour,
	the lower half from the full colour down to 15% brightness."""
	x = min(max(int(x), 0), PICKER_WIDTH - 1)
	y = min(max(int(y), 0), PICKER_HEIGHT - 1)
	h = float(x) / (PICKER_WIDTH - 1)
	half = PICKER_HEIGHT // 2
	if y < half:
		return _hsv(h, float(y) / half, 1.0)
	return _hsv(h, 1.0, 1.0 - 0.85 * float(y - half) / (PICKER_HEIGHT - 1 - half))


def ToRGB(value):
	"""0xRRGGBB -> (r, g, b)"""
	return ((value >> 16) & 0xff, (value >> 8) & 0xff, value & 0xff)


def FromRGB(rgb):
	return ((int(rgb[0]) & 0xff) << 16) | ((int(rgb[1]) & 0xff) << 8) | (int(rgb[2]) & 0xff)


def ToHex(value):
	return "#%06X" % (value & 0xffffff)


def ParseHex(text):
	"""'#RRGGBB' / 'RRGGBB' / '#RGB' -> 0xRRGGBB, or -1 when it is not a colour"""
	t = text.strip().lstrip("#")
	if len(t) == 3:
		t = t[0] * 2 + t[1] * 2 + t[2] * 2
	if len(t) != 6:
		return -1
	try:
		return int(t, 16)
	except ValueError:
		return -1


def IsBrightEnough(value):
	return max(ToRGB(value)) >= MIN_BRIGHTNESS
