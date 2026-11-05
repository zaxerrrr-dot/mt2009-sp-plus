# MT2009_PLUS_LANG_V1 - the client's language (client-patches/lang, tools/lang/build_lang_packs.py).
#
# The language is the LANGUAGE line of game1.cfg (systemSetting.Get/SetLanguage). The build makes, for every language,
# a complete locale/<code>/ in the pack "lang" (locale_game / locale_interface over the Polish ones, item / monster
# names, item and skill descriptions for the exe, the description files) and locale/<code>/mt2009_texts.txt: every
# Polish string of this root's python with its translation. Here:
#   Language() / Languages()     the language of this client run / the ones the choice offers (the list file of the
#                                build; an exe without the per-language codepage - no app.MT2009_LANG_CODEPAGE - only
#                                gets the languages that read right under codepage 1250)
#   Translate(text)              the UI sink: ui.TextLine.SetText (every label, button, tooltip, dialog, board title
#                                and uiscript "text") and chat.AppendChat of python messages pass their text through
#                                it - a Polish string of the root becomes the language's (exact; a %-template of the
#                                list matches a formatted one; "Label: " + value by its label)
#   T(pl, en)                    playerbot_lang.T: the language's text of a Polish / English pair
#   LocalePath(path)             locale/pl/<file> -> locale/<language>/<file> when the language has it
#   SetLanguage(code)            saves the user's choice (game1.cfg) and, in the game, tells the server ("/lang <code>")
#   SendToServer()               "/lang <code>" - game.py at every entry into the game, only for a language the user
#                                chose himself (else the server gives the player its default language)
#   OnServerLanguage(def, own)   the server's "MT2009LANG <default> <own|->" at the entry: a client whose user never
#                                chose a language takes the player's own one, else the server's default (game1.cfg,
#                                at the next start)
# MT2009_PLUS_LANGUAGE_DEFAULT_V1: who set game1.cfg's LANGUAGE is kept in mt2009_language.cfg beside it - "user <code>"
# (the login screen / Options choice: it always wins) or "server <code>" (the server's default, or the launcher's for
# the server it set up, may change it again). Without the file a language other than Polish counts as the user's (a
# client set before the file existed).
# Polish (the source) passes everything through unchanged. A change of language takes effect at the next start of the
# client (the exe reads the names, descriptions and the codepage at start): Restart() starts it again on an exe with
# app.Mt2009Restart, else the player is asked to.
#
# Python 2.7 as the client has it; the file is ASCII (Polish strings as CP1250 escapes).
import app

try:
	import systemSetting
except ImportError:
	systemSetting = None

SOURCE = "pl"
ORIGIN_FILE = "mt2009_language.cfg"
LIST_FILE = "locale/common/mt2009_languages.txt"
TEXTS_FILE = "locale/%s/mt2009_texts.txt"
CACHE_LIMIT = 6000

_state = {
	"lang": None,		# the language of this run (fixed at the first call)
	"chosen": None,		# the language saved for the next start
	"texts": None,		# exact Polish -> translation
	"templates": None,	# [(regex, [placeholder names], translation)] by the first two characters
	"generic": None,	# templates that start with a placeholder
	"labels": None,		# "Label:" / "Label: " -> translation
	"cache": {},
	"list": None,
}


def _Exists(path):
	try:
		import pack
		return pack.Exist(path)
	except Exception:
		return False


def _Read(path):
	try:
		import pack
		if pack.Exist(path):
			return pack.Get(path) or ""
	except Exception:
		pass
	try:
		f = open(path, "rb")
		try:
			return f.read()
		finally:
			f.close()
	except Exception:
		return ""


def _Unescape(s):
	if "\\" not in s:
		return s
	out = []
	i = 0
	n = len(s)
	while i < n:
		c = s[i]
		if c == "\\" and i + 1 < n:
			nx = s[i + 1]
			if nx == "t":
				out.append("\t")
			elif nx == "n":
				out.append("\n")
			elif nx == "r":
				out.append("\r")
			elif nx == "\\":
				out.append("\\")
			else:
				out.append(c + nx)
			i += 2
		else:
			out.append(c)
			i += 1
	return "".join(out)


def ExeSwitchesCodePage():
	"""the exe sets the codepage of the language at start (exe-src21, MT2009_PLUS_LANG_V1)"""
	return bool(getattr(app, "MT2009_LANG_CODEPAGE", 0))


def CanRestart():
	return hasattr(app, "Mt2009Restart")


def _CodePage():
	try:
		return int(app.GetDefaultCodePage())
	except Exception:
		return 1250


def Languages():
	"""[(code, name, codepage)] the choice offers, in the list's order (Polish first); the name in the codepage of
	this run when it has it, else in ASCII"""
	if _state["list"] is not None:
		return _state["list"]
	out = []
	cps = []
	cur = _CodePage()
	switch = ExeSwitchesCodePage()
	for line in _Read(LIST_FILE).replace("\r", "").split("\n"):
		if not line:
			continue
		cols = line.split("\t")
		if line.startswith("#CODEPAGES"):
			cps = cols[1:]
			continue
		if line.startswith("#") or len(cols) < 4:
			continue
		code, cp, safe, ascii_name = cols[0], cols[1], cols[2], cols[3]
		if code != SOURCE and not switch and safe != "1":
			continue
		name = ascii_name
		if str(cur) in cps:
			idx = 4 + cps.index(str(cur))
			if idx < len(cols) and cols[idx]:
				name = cols[idx]
		try:
			cp = int(cp)
		except ValueError:
			cp = 1252
		out.append((code, name, cp))
	if not out:
		out = [(SOURCE, "Polski", 1250)]
	_state["list"] = out
	return out


def _Configured():
	lang = ""
	if systemSetting:
		try:
			lang = systemSetting.GetLanguage() or ""
		except Exception:
			lang = ""
	return lang.lower() or SOURCE


def _Usable(code):
	"""the packs have the language and this exe can show it (Languages() leaves out what a 1250-only exe cannot)"""
	if code == SOURCE:
		return True
	if not _Exists("locale/%s/skilldesc.txt" % code):
		return False
	for c, name, cp in Languages():
		if c == code:
			return True
	return False


def Language():
	"""the language of this client run (the exe read the same one at start)"""
	if _state["lang"] is None:
		lang = _Configured()
		if not _Usable(lang):
			# a language the packs do not have (or one this exe cannot show): Polish, saved
			lang = SOURCE
			_Save(lang)
		_state["lang"] = lang
		_state["chosen"] = lang
	return _state["lang"]


def ChosenLanguage():
	Language()
	return _state["chosen"]


def IsSource():
	return Language() == SOURCE


def LanguageName(code):
	for c, name, cp in Languages():
		if c == code:
			return name
	return code


def _Save(code):
	if not systemSetting:
		return
	try:
		systemSetting.SetLanguage(code)
		if hasattr(systemSetting, "SaveConfig"):
			systemSetting.SaveConfig()
	except Exception:
		pass


def _Open(path, mode):
	try:
		import __builtin__
		return getattr(__builtin__, "old_open", open)(path, mode)
	except Exception:
		return open(path, mode)


def _ReadOrigin():
	"""("user" | "server", code) of mt2009_language.cfg, or (None, None)"""
	try:
		f = _Open(ORIGIN_FILE, "r")
		try:
			parts = f.read().split()
		finally:
			f.close()
	except Exception:
		return None, None
	if len(parts) >= 2 and parts[0] in ("user", "server"):
		return parts[0], parts[1].lower()
	return None, None


def _WriteOrigin(origin, code):
	try:
		f = _Open(ORIGIN_FILE, "w")
		try:
			f.write("%s %s\n" % (origin, code))
		finally:
			f.close()
	except Exception:
		pass


def UserChose():
	"""whether the language of game1.cfg is the user's own choice (not the server's default)"""
	origin, code = _ReadOrigin()
	if origin is not None:
		return origin == "user"
	# a client set up before mt2009_language.cfg existed: any language but Polish was somebody's choice
	return _Configured() != SOURCE


def SendToServer(code=None):
	"""tell the server the player's language (the server's texts, bots and quests follow it); without a code only
	the user's own choice is sent - a client that never had one leaves the player on the server's default"""
	if code is None:
		if not UserChose():
			return
		code = ChosenLanguage()
	try:
		import net
		net.SendChatPacket("/lang %s" % code)
	except Exception:
		pass


def SetLanguage(code, inGame=False):
	"""save the user's choice for the next start; True when it differs from this run's language (a restart is
	needed)"""
	Language()
	code = (code or SOURCE).lower()
	_state["chosen"] = code
	_Save(code)
	_WriteOrigin("user", code)
	if inGame:
		SendToServer(code)
	return code != _state["lang"]


def _Normalize(code):
	code = (code or "").strip().lower()
	return {"cs": "cz", "el": "gr", "ar": "ae"}.get(code, code)


def OnServerLanguage(default, own="-"):
	"""MT2009_PLUS_LANGUAGE_DEFAULT_V1: the server's "MT2009LANG <default> <own|->" at the entry into the game. A client
	whose user never chose a language takes the player's own language (chosen on another computer), else the server's
	default, for its own texts at the next start. True when game1.cfg changed (the language window is shown then)."""
	if UserChose():
		return False
	own = _Normalize(own)
	target = own if own and own != "-" else _Normalize(default)
	if not target or not _Usable(target):
		return False
	Language()
	if target == _state["chosen"]:
		_WriteOrigin("server", target)
		return False
	_state["chosen"] = target
	_Save(target)
	_WriteOrigin("server", target)
	return target != _state["lang"]


def Restart():
	"""start the client again (exe-src21); False when this exe cannot"""
	if CanRestart():
		try:
			return bool(app.Mt2009Restart())
		except Exception:
			return False
	return False


def LocalePath(path):
	"""locale/pl/<file> -> locale/<language>/<file> when the language has that file"""
	lang = Language()
	if lang == SOURCE or not path:
		return path
	low = path.replace("\\", "/")
	if low.lower().startswith("locale/pl/"):
		cand = "locale/%s/%s" % (lang, low[10:])
		if _Exists(cand):
			return cand
	return path


# ---------------------------------------------------------------- the texts of the root python

def _Placeholders(s):
	"""[(start, end, name or None, is_literal_percent)] of the %-placeholders of a template"""
	out = []
	i = 0
	n = len(s)
	while i < n:
		if s[i] != "%":
			i += 1
			continue
		j = i + 1
		if j < n and s[j] == "%":
			out.append((i, j + 1, None, True))
			i = j + 1
			continue
		name = None
		if j < n and s[j] == "(":
			k = s.find(")", j)
			if k < 0:
				i = j
				continue
			name = s[j + 1:k]
			j = k + 1
		while j < n and s[j] in "-+#0":
			j += 1
		while j < n and (s[j].isdigit() or s[j] == "*"):
			j += 1
		if j < n and s[j] == ".":
			j += 1
			while j < n and s[j].isdigit():
				j += 1
		if j < n and s[j] in "sdifxXcurgeEGo":
			out.append((i, j + 1, name, False))
			i = j + 1
		else:
			i = j
	return out


def _Compile(pl):
	import re
	phs = _Placeholders(pl)
	if not [p for p in phs if not p[3]]:
		return None, None
	parts = []
	names = []
	last = 0
	for start, end, name, literal in phs:
		parts.append(re.escape(pl[last:start]))
		if literal:
			parts.append("%")
		else:
			parts.append("(.*?)")
			names.append(name)
		last = end
	parts.append(re.escape(pl[last:]))
	try:
		return re.compile("^" + "".join(parts) + "$", re.S), names
	except Exception:
		return None, None


def _Fill(tr, names, values):
	byname = {}
	for nm, v in zip(names, values):
		if nm:
			byname[nm] = v
	out = []
	last = 0
	pos = 0
	for start, end, name, literal in _Placeholders(tr):
		out.append(tr[last:start])
		if literal:
			out.append("%")
		elif name is not None:
			out.append(byname.get(name, ""))
		else:
			out.append(values[pos] if pos < len(values) else "")
			pos += 1
		last = end
	out.append(tr[last:])
	return "".join(out)


def _Letters(s):
	n = 0
	for c in s:
		if c.isalpha() or c >= "\x80":
			n += 1
	return n


def _Load():
	texts = {}
	templates = {}
	generic = []
	labels = {}
	fragments = []
	lang = Language()
	if lang != SOURCE:
		data = _Read(TEXTS_FILE % lang)
		for line in data.split("\n"):
			line = line.rstrip("\r")
			if not line:
				continue
			tab = line.find("\t")
			if tab <= 0:
				continue
			pl = _Unescape(line[:tab])
			tr = _Unescape(line[tab + 1:])
			texts[pl] = tr
			# a dialog shows a text line by line (uiCommon.PopupDialog splits it at [ENTER], others at a newline): the
			# lines of a text with the same number of lines in both languages are entries too
			for sep in ("[ENTER]", "\n"):
				if sep in pl:
					pls = pl.split(sep)
					trs = tr.split(sep)
					if len(pls) == len(trs):
						for a, b in zip(pls, trs):
							if a.strip() and a not in texts:
								fragments.append((a, b))
			if "%" in pl:
				if "%%" in pl and not [p for p in _Placeholders(pl) if not p[3]]:
					# shown after a % formatting: "100%% ..." reads "100% ..."
					texts[pl.replace("%%", "%")] = tr.replace("%%", "%")
				rx, names = _Compile(pl)
				# a template must have letters of its own ("%s" alone would match every text)
				if rx is not None and _Letters(_StripPlaceholders(pl)) >= 2:
					head = pl[:2]
					if "%" in head:
						generic.append((rx, names, tr))
					else:
						templates.setdefault(head, []).append((rx, names, tr))
			stripped = pl.rstrip(" ")
			if stripped.endswith(":") and len(stripped) > 1:
				labels[stripped] = tr.rstrip(" ")
	for a, b in fragments:
		if a not in texts:
			texts[a] = b
	_state["texts"] = texts
	_state["templates"] = templates
	_state["generic"] = generic
	_state["labels"] = labels


def _StripPlaceholders(s):
	out = []
	last = 0
	for start, end, name, literal in _Placeholders(s):
		out.append(s[last:start])
		last = end
	out.append(s[last:])
	return "".join(out)


def _Lookup(text, depth=0):
	texts = _state["texts"]
	tr = texts.get(text)
	if tr is not None:
		return tr
	if depth > 2:
		return None
	# a formatted template; its values are looked up too ("%s" of a Polish word)
	for rx, names, trt in tuple(_state["templates"].get(text[:2], ())) + tuple(_state["generic"]):
		m = rx.match(text)
		if m:
			values = []
			for v in m.groups():
				if v and len(v) < len(text) and _Letters(v) >= 2:
					values.append(_Lookup(v, depth + 1) or v)
				else:
					values.append(v)
			return _Fill(trt, names, values)
	# "Label: value" / "Label:value"
	colon = text.find(":")
	if 0 < colon < len(text) - 1:
		lab = _state["labels"].get(text[:colon + 1])
		if lab is not None:
			rest = text[colon + 1:]
			return lab + rest
	return None


def Translate(text):
	"""the language's text of a Polish string of the root (unchanged when there is none or the client is Polish)"""
	if _state["lang"] == SOURCE:
		return text
	if text.__class__ is not str or not text:
		return text
	if _state["texts"] is None:
		if Language() == SOURCE:
			return text
		_Load()
	cache = _state["cache"]
	tr = cache.get(text)
	if tr is not None:
		return tr
	tr = text
	if len(text) > 1:
		has_letter = False
		for c in text:
			if c.isalpha() or c >= "\x80":
				has_letter = True
				break
		if has_letter:
			found = _Lookup(text)
			if found is not None:
				tr = found
	if len(cache) > CACHE_LIMIT:
		cache.clear()
	cache[text] = tr
	return tr


def T(pl, en):
	"""a Polish / English pair (playerbot_lang.T): Polish, the language's text of the Polish one, else English"""
	lang = Language()
	if lang == SOURCE:
		return pl
	if _state["texts"] is None:
		_Load()
	tr = _state["texts"].get(pl)
	if tr is not None:
		return tr
	return en


# ---------------------------------------------------------------- chat messages of the root python

def _WrapChat():
	try:
		import chat
	except ImportError:
		return
	orig = getattr(chat, "AppendChat", None)
	if orig is None or getattr(orig, "_mt2009lang", False):
		return

	def AppendChat(chatType, text, *args):
		return orig(chatType, Translate(text), *args)

	AppendChat._mt2009lang = True
	try:
		chat.AppendChat = AppendChat
	except Exception:
		pass


def Install():
	"""called by ui.py at import: the chat sink (the text sink is ui.TextLine.SetText)"""
	if Language() != SOURCE:
		_WrapChat()
